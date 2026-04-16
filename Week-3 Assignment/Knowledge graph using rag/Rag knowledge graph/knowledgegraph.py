"""Hybrid RAG + Knowledge Graph pipeline using LangChain.

This script does all core steps required for a practical knowledge graph RAG flow:
1) Load documents from a directory.
2) Split documents into chunks.
3) Build a vector index for semantic retrieval.
4) Extract (subject, predicate, object) triples with an LLM.
5) Build an in-memory knowledge graph.
6) Answer queries using both vector context and graph context.

Environment variables:
- OPENAI_API_KEY: Enables ChatOpenAI + OpenAIEmbeddings.
- OPENAI_MODEL: Optional (default: gpt-4o-mini).
- OLLAMA_MODEL: Fallback LLM if OpenAI key is not provided.

Install (example):
pip install langchain langchain-community langchain-openai langchain-text-splitters faiss-cpu networkx
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
	from langchain_community.document_loaders import (
		DirectoryLoader,
		PyPDFLoader,
		TextLoader,
	)
	from langchain_community.vectorstores import FAISS
except ImportError as exc:
	raise ImportError(
		"Missing loader/vector dependencies. Install with: "
		"pip install langchain-community faiss-cpu"
	) from exc

try:
	from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:
	ChatOpenAI = None
	OpenAIEmbeddings = None

try:
	from langchain_ollama import ChatOllama
except ImportError:
	ChatOllama = None

try:
	from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
	HuggingFaceEmbeddings = None


@dataclass
class Triple:
	subject: str
	predicate: str
	object: str
	evidence: str


class HybridKnowledgeGraphRAG:
	"""Builds and queries a hybrid vector + knowledge graph RAG system."""

	def __init__(
		self,
		data_path: str,
		persist_path: str = "./artifacts",
		chunk_size: int = 900,
		chunk_overlap: int = 150,
	) -> None:
		self.data_path = Path(data_path)
		self.persist_path = Path(persist_path)
		self.persist_path.mkdir(parents=True, exist_ok=True)

		self.chunker = RecursiveCharacterTextSplitter(
			chunk_size=chunk_size,
			chunk_overlap=chunk_overlap,
		)

		self.llm = self._build_llm()
		self.embeddings = self._build_embeddings()

		self.documents: List[Document] = []
		self.chunks: List[Document] = []
		self.vector_store: Optional[FAISS] = None
		self.graph = nx.MultiDiGraph()

	def _build_llm(self):
		openai_api_key = os.getenv("OPENAI_API_KEY")
		if openai_api_key:
			if ChatOpenAI is None:
				raise ImportError(
					"OPENAI_API_KEY is set but langchain-openai is not installed. "
					"Install with: pip install langchain-openai"
				)
			return ChatOpenAI(
				model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
				temperature=0,
			)

		ollama_model = os.getenv("OLLAMA_MODEL")
		if ollama_model:
			if ChatOllama is None:
				raise ImportError(
					"OLLAMA_MODEL is set but ChatOllama is unavailable. "
					"Install with: pip install langchain-community"
				)
			return ChatOllama(model=ollama_model, temperature=0)

		raise RuntimeError(
			"No LLM configured. Set OPENAI_API_KEY (recommended) or OLLAMA_MODEL."
		)

	def _build_embeddings(self):
		if os.getenv("OPENAI_API_KEY"):
			if OpenAIEmbeddings is None:
				raise ImportError(
					"OPENAI embeddings requested but langchain-openai is missing."
				)
			return OpenAIEmbeddings(model="text-embedding-3-small")

		if HuggingFaceEmbeddings is None:
			raise ImportError(
				"HuggingFace embeddings backend is missing. Install with: "
				"pip install langchain-huggingface"
			)
		return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

	def load_documents(self) -> List[Document]:
		"""Load many common file types from the data directory."""
		if not self.data_path.exists():
			raise FileNotFoundError(f"Data path does not exist: {self.data_path}")

		docs: List[Document] = []

		text_globs = ["**/*.txt", "**/*.md", "**/*.py", "**/*.json", "**/*.csv", "**/*.html"]
		for pattern in text_globs:
			loader = DirectoryLoader(
				str(self.data_path),
				glob=pattern,
				loader_cls=TextLoader,
				loader_kwargs={"encoding": "utf-8"},
				show_progress=True,
				use_multithreading=True,
				silent_errors=True,
			)
			docs.extend(loader.load())

		pdf_loader = DirectoryLoader(
			str(self.data_path),
			glob="**/*.pdf",
			loader_cls=PyPDFLoader,
			show_progress=True,
			use_multithreading=True,
			silent_errors=True,
		)
		docs.extend(pdf_loader.load())

		self.documents = [d for d in docs if d.page_content and d.page_content.strip()]
		if not self.documents:
			raise ValueError(
				f"No readable documents found in {self.data_path}. Add files and retry."
			)
		return self.documents

	def split_documents(self) -> List[Document]:
		if not self.documents:
			self.load_documents()

		chunks = self.chunker.split_documents(self.documents)
		for idx, chunk in enumerate(chunks):
			chunk.metadata = dict(chunk.metadata)
			chunk.metadata["chunk_id"] = idx

		self.chunks = chunks
		return self.chunks

	def build_vector_index(self) -> FAISS:
		if not self.chunks:
			self.split_documents()

		self.vector_store = FAISS.from_documents(self.chunks, self.embeddings)
		self.vector_store.save_local(str(self.persist_path / "faiss_index"))
		return self.vector_store

	def _llm_text(self, response: BaseMessage | str) -> str:
		if isinstance(response, str):
			return response
		return getattr(response, "content", str(response))

	def _extract_json(self, text: str):
		text = text.strip()
		try:
			return json.loads(text)
		except json.JSONDecodeError:
			pass

		# Fallback for markdown-style fenced JSON.
		match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
		if match:
			return json.loads(match.group(1))

		# Last resort: first list-like structure.
		list_match = re.search(r"\[(.*)\]", text, flags=re.DOTALL)
		if list_match:
			return json.loads("[" + list_match.group(1) + "]")
		return []

	def extract_triples(self, max_chunks: Optional[int] = 120) -> List[Triple]:
		if not self.chunks:
			self.split_documents()

		prompt = ChatPromptTemplate.from_template(
			"""
			Extract factual knowledge triples from the text.
			Return JSON only as a list of objects with keys:
			subject, predicate, object, evidence.

			Rules:
			- Keep subject/object concise entities.
			- Use relation-like predicate phrases.
			- Ignore uncertain facts.
			- If nothing is found, return [].

			TEXT:
			{text}
			"""
		)

		triples: List[Triple] = []
		chunk_iterable = self.chunks if max_chunks is None else self.chunks[:max_chunks]

		for chunk in chunk_iterable:
			chain = prompt | self.llm
			raw = chain.invoke({"text": chunk.page_content[:4000]})
			parsed = self._extract_json(self._llm_text(raw))
			if not isinstance(parsed, list):
				continue
			for row in parsed:
				if not isinstance(row, dict):
					continue
				s = str(row.get("subject", "")).strip()
				p = str(row.get("predicate", "")).strip()
				o = str(row.get("object", "")).strip()
				e = str(row.get("evidence", "")).strip()
				if s and p and o:
					triples.append(Triple(subject=s, predicate=p, object=o, evidence=e))

		return triples

	def build_graph(self, triples: List[Triple]) -> nx.MultiDiGraph:
		for t in triples:
			self.graph.add_node(t.subject, label=t.subject)
			self.graph.add_node(t.object, label=t.object)
			self.graph.add_edge(
				t.subject,
				t.object,
				predicate=t.predicate,
				evidence=t.evidence,
			)

		self._persist_graph()
		return self.graph

	def _persist_graph(self) -> None:
		path = self.persist_path / "knowledge_graph.graphml"
		nx.write_graphml(self.graph, path)

	def _entity_candidates(self, query: str) -> List[str]:
		prompt = ChatPromptTemplate.from_template(
			"""
			Extract important entities from this user question.
			Return JSON list of strings only.
			QUESTION: {question}
			"""
		)
		chain = prompt | self.llm
		raw = chain.invoke({"question": query})
		parsed = self._extract_json(self._llm_text(raw))
		if isinstance(parsed, list):
			return [str(x).strip() for x in parsed if str(x).strip()]
		return []

	def _graph_context(self, query: str, max_facts: int = 20) -> str:
		if self.graph.number_of_nodes() == 0:
			return ""

		entities = self._entity_candidates(query)
		if not entities:
			return ""

		facts: List[str] = []
		lower_node_map: Dict[str, str] = {n.lower(): n for n in self.graph.nodes}

		matched_nodes = []
		for ent in entities:
			if ent.lower() in lower_node_map:
				matched_nodes.append(lower_node_map[ent.lower()])

		for node in matched_nodes:
			for source, target, data in self.graph.out_edges(node, data=True):
				facts.append(
					f"{source} --[{data.get('predicate', 'related_to')}]--> {target}"
				)
			for source, target, data in self.graph.in_edges(node, data=True):
				facts.append(
					f"{source} --[{data.get('predicate', 'related_to')}]--> {target}"
				)

		unique = list(dict.fromkeys(facts))
		return "\n".join(unique[:max_facts])

	def _vector_context(self, query: str, k: int = 5) -> str:
		if self.vector_store is None:
			raise RuntimeError("Vector store not built yet. Run index_all() first.")

		docs = self.vector_store.similarity_search(query, k=k)
		blocks = []
		for doc in docs:
			source = doc.metadata.get("source", "unknown")
			chunk_id = doc.metadata.get("chunk_id", "na")
			blocks.append(f"[source={source} chunk={chunk_id}]\n{doc.page_content}")
		return "\n\n".join(blocks)

	def debug_retrieval(self, query: str, k: int = 5, max_facts: int = 20) -> Dict[str, str]:
		"""Return retrieval context pieces to help inspect why an answer was produced."""
		return {
			"graph_context": self._graph_context(query, max_facts=max_facts),
			"vector_context": self._vector_context(query, k=k),
		}

	def answer(self, query: str) -> str:
		if self.vector_store is None:
			raise RuntimeError("System not indexed. Run index_all() before asking questions.")

		contexts = self.debug_retrieval(query=query, k=5, max_facts=20)
		vector_ctx = contexts["vector_context"]
		graph_ctx = contexts["graph_context"]

		prompt = ChatPromptTemplate.from_template(
			"""
			You are a precise analyst. Use the provided context to answer the question.

			GRAPH FACTS:
			{graph_context}

			RETRIEVED PASSAGES:
			{vector_context}

			USER QUESTION:
			{question}

			Instructions:
			- Prefer retrieved passages as primary evidence.
			- Answer directly and include key facts found in context.
			- If context is partial, provide the best-supported answer and state any uncertainty briefly.
			- Only say "I do not have enough information" when both graph facts and retrieved passages are clearly insufficient.
			- Do not invent facts that are not present.
			"""
		)

		chain = prompt | self.llm
		result = chain.invoke(
			{
				"graph_context": graph_ctx or "(no graph facts matched)",
				"vector_context": vector_ctx,
				"question": query,
			}
		)
		return self._llm_text(result)

	def index_all(self, max_chunks_for_graph: Optional[int] = 120) -> Tuple[int, int, int]:
		self.load_documents()
		self.split_documents()
		self.build_vector_index()

		triples = self.extract_triples(max_chunks=max_chunks_for_graph)
		self.build_graph(triples)

		return len(self.documents), len(self.chunks), len(triples)


def build_arg_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Build and query a LangChain RAG knowledge graph.")
	parser.add_argument(
		"--data-path",
		type=str,
		required=True,
		help="Folder containing your documents.",
	)
	parser.add_argument(
		"--persist-path",
		type=str,
		default="./artifacts",
		help="Folder to store FAISS index and graph files.",
	)
	parser.add_argument(
		"--query",
		type=str,
		default=None,
		help="Question to ask after indexing. If omitted, starts interactive mode.",
	)
	parser.add_argument(
		"--graph-max-chunks",
		type=int,
		default=120,
		help="How many chunks to use for triple extraction.",
	)
	return parser


def interactive_loop(system: HybridKnowledgeGraphRAG) -> None:
	print("\nKnowledge Graph RAG ready. Type a question (or 'exit').")
	while True:
		query = input("\nQ> ").strip()
		if query.lower() in {"exit", "quit"}:
			break
		if not query:
			continue
		print("\nA>", system.answer(query))


def main() -> None:
	args = build_arg_parser().parse_args()

	system = HybridKnowledgeGraphRAG(
		data_path=args.data_path,
		persist_path=args.persist_path,
	)

	doc_count, chunk_count, triple_count = system.index_all(
		max_chunks_for_graph=args.graph_max_chunks
	)
	print(
		f"Indexed {doc_count} documents, {chunk_count} chunks, "
		f"and extracted {triple_count} triples."
	)

	if args.query:
		print(system.answer(args.query))
	else:
		interactive_loop(system)


if __name__ == "__main__":
	main()
