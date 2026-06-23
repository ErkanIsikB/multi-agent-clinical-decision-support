# Model and Technology Selection

## Decision

ClinicalBridge defaults to `gpt-5.4-mini` for agent calls and `text-embedding-3-small` for EHR embeddings. Both identifiers are configurable through `.env`.

## Rationale

The prototype makes several model calls for each non-critical alert: triage, EHR extraction, anamnesis interpretation, and synthesis. A smaller current model offers a more appropriate cost-latency balance for repeated structured extraction and summarization than the flagship model. The architecture preserves the option to switch to `gpt-5.5` for comparative experiments without code changes.

The model integration uses:

- the OpenAI Responses API path through `langchain-openai`;
- native JSON-schema output for triage, anamnesis, and synthesis, plus OpenAI function calling for the heterogeneous EHR schema, all mapped to Pydantic models;
- low reasoning effort for bounded extraction and synthesis tasks;
- provider retries plus deterministic safety validation.

`text-embedding-3-small` was selected because the dataset is small, the retrieval task is narrow, and the capstone values an understandable cost-performance choice over maximal embedding dimensionality.

## Considered alternatives

### GPT-5.5

The current flagship model is suitable for complex reasoning and could improve nuanced synthesis, but its higher per-call cost is difficult to justify for every agent in a student prototype. It remains an environment-variable option for final comparison.

### GPT-5.4 nano

The nano variant would reduce cost further, but the synthesis and anamnesis roles require nuanced instruction-following, uncertainty language, and reliable schema adherence. The mini variant is the safer default compromise.

### Direct OpenAI SDK without LangChain

The direct SDK would reduce framework surface area. It was not chosen as the sole implementation because the capstone explicitly requires LangChain pipelines and multi-agent orchestration. LangChain also provides a uniform structured-output interface, while LangGraph expresses parallel and conditional workflow edges clearly.

### OpenAI hosted file search

Hosted file search could simplify retrieval, but a local Chroma index makes the chunking, metadata filtering, retrieval parameters, and evaluation mechanics visible for the portfolio. It also keeps the simulated dataset inspectable within the submission.

## Parameter policy

The project does not force a temperature on current reasoning models. Instead it uses low reasoning effort, schema-constrained output, precise prompts, few-shot examples, and deterministic evaluation. This choice is documented because unsupported or model-specific sampling settings can make a seemingly reproducible configuration misleading.

## Sources consulted

- [OpenAI Models](https://developers.openai.com/api/docs/models)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI Embeddings](https://developers.openai.com/api/docs/guides/embeddings)
- [OpenAI Text Generation](https://developers.openai.com/api/docs/guides/text?api-mode=responses)
- [LangChain ChatOpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [LangChain Chroma integration](https://docs.langchain.com/oss/python/integrations/vectorstores/chroma)
- [LangGraph workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
