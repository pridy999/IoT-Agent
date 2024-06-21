from imports import *

from common.utils import * 
from common.args import args 


if __name__ == "__main__":
    # data_dict, label_dict = read_machine_data()
    data_dict, label_dict = read_IoT_data(args.task_type, args.cls_num) # type: ignore
    start_time = time.perf_counter()
    config = f"""
task_type: {args.task_type}
sample_num: {args.sample_num}
no_domain_knowledge: {args.no_domain_knowledge}
no_demo_knowledge: {args.no_demo_knowledge}
model: {args.model} on {args.device}
generate results are saved in {args.output_file_path}"""
    # with rerieval:
    # 首先，准备好document_store并写入:
    # 得到指定文件夹下所有文件的路径
    if not args.no_domain_knowledge:
        KB_paths = get_knowledge_paths(args)    
        document_store_domain = InMemoryDocumentStore()
        splitter_kwags_domain = {"split_by": "sentence", "split_length": 2}
        embedded_document_store_KB = prepare_and_embed_documents(document_store_domain, KB_paths, device=args.device, splitter_kwards=splitter_kwags_domain)
    if not args.no_demo_knowledge: # TODO
        document_store_demo = InMemoryDocumentStore()
        splitter_kwags_demo = {"split_by": "passage", "split_length": 1}
        Demo_paths = get_knowledge_paths(args, False)
        meta_data = None # TODO
        embedded_document_store_DM = prepare_and_embed_documents(document_store_demo, Demo_paths, device=args.device, splitter_kwards=splitter_kwags_demo, meta_data=meta_data)

    
    ans = []
    with open(args.output_file_path, "a") as f:
        for i in range(1, args.sample_num+1):


            #### 这一段目前是task_dependent的，需要根据具体的task来修改
            if args.task_type == "machine_detection":
                grd = "Pos"
                con = "Neg"
                # template, data_des = gen_prompt_tamplate_with_rag_machine(data_dict, label_dict, "Cooler condition %", i, grd)
                template, data_des = generate_prompt_template(
                    args,
                    data_dict,
                    label_dict,
                    "Cooler condition %",
                    i,
                    grd
                ) # type: ignore
                query = """Is the machine's cooling system functioning properly?"""
            elif args.task_type == "imu_HAR":
                if args.cls_num == 2:
                    grd = "WALKING"
                    con = "STANDING"
                    template, data_des = gen_prompt_template_with_rag(data_dict, grd, con, i) # type: ignore
                    query = """
Based on the given data,choose the activity that the subject is most likely to be performing from the following two options:"""

            ####

            prompt_builder = PromptBuilder(template=template)
            generator = ChatModel(args.model, args.device)
            
            # 创建pipeline:
            rag_pipeline = Pipeline()
            rag_pipeline.add_component("prompt_builder", prompt_builder)
            run_kwargs =  {"prompt_builder": {"query": query}}

            if not args.no_domain_knowledge:
                text_embedder = SentenceTransformersTextEmbedder(model=EMBEDDER_MODEL_LOCAL, device=ComponentDevice.from_str(args.device))

                embedding_retriever_domain = InMemoryEmbeddingRetriever(embedded_document_store_KB)

                keyword_retriever_domain = InMemoryBM25Retriever(embedded_document_store_KB)
                
                document_joiner_domain = DocumentJoiner()

                ranker_domain = TransformersSimilarityRanker(model=RANKER_MODEL_LOCAL)

                # 1. for domain-knowledge:
                rag_pipeline.add_component("text_embedder_domain", text_embedder)
                rag_pipeline.add_component("embedding_retriever_domain", embedding_retriever_domain)
                rag_pipeline.add_component("keyword_retriever_domain", keyword_retriever_domain)
                rag_pipeline.add_component("document_joiner_domain", document_joiner_domain)
                rag_pipeline.add_component("ranker_domain", ranker_domain)

                # 将components连接起来
                # 1. for domain-knowledge:
                rag_pipeline.connect("text_embedder_domain", "embedding_retriever_domain")
                rag_pipeline.connect("embedding_retriever_domain", "document_joiner_domain")
                rag_pipeline.connect("keyword_retriever_domain", "document_joiner_domain")
                rag_pipeline.connect("document_joiner_domain", "ranker_domain")
                content4retrieval_domain = gen_content4retrive_domain(args.task_type, data_des)
                rag_pipeline.connect("ranker_domain", "prompt_builder.documents_domain")

                run_kwargs["text_embedder_domain"] = {"text": content4retrieval_domain}
                run_kwargs["keyword_retriever_domain"] = {"query": content4retrieval_domain}
                run_kwargs["ranker_domain"] = {"query": content4retrieval_domain}

            if not args.no_demo_knowledge: # TODO
                grd_demo_embedder = SentenceTransformersTextEmbedder(model=EMBEDDER_MODEL_LOCAL, device=ComponentDevice.from_str(args.device))
                con_demo_embedder = SentenceTransformersTextEmbedder(model=EMBEDDER_MODEL_LOCAL, device=ComponentDevice.from_str(args.device))

                grd_embedding_retriever_demo = InMemoryEmbeddingRetriever(embedded_document_store_DM)
                con_embedding_retriever_demo = InMemoryEmbeddingRetriever(embedded_document_store_DM)

                grd_keyword_retriever_demo = InMemoryBM25Retriever(embedded_document_store_DM)
                con_keyword_retriever_demo = InMemoryBM25Retriever(embedded_document_store_DM)

                grd_document_joiner_demo = DocumentJoiner()
                con_document_joiner_demo = DocumentJoiner()
            
                grd_ranker_demo = TransformersSimilarityRanker(model=RANKER_MODEL_LOCAL)
                con_ranker_demo = TransformersSimilarityRanker(model=RANKER_MODEL_LOCAL)

                # 2. for demo-knowledge:
                # 2.1 for ground-truth demo knowledge:
                rag_pipeline.add_component("grd_demo_embedder", grd_demo_embedder)
                rag_pipeline.add_component("grd_embedding_retriever_demo", grd_embedding_retriever_demo)
                rag_pipeline.add_component("grd_keyword_retriever_demo", grd_keyword_retriever_demo)
                rag_pipeline.add_component("grd_document_joiner_demo", grd_document_joiner_demo)
                rag_pipeline.add_component("grd_ranker_demo", grd_ranker_demo)
                # 2.2 for contrast demo knowledge:
                rag_pipeline.add_component("con_demo_embedder", con_demo_embedder)
                rag_pipeline.add_component("con_embedding_retriever_demo", con_embedding_retriever_demo)
                rag_pipeline.add_component("con_keyword_retriever_demo", con_keyword_retriever_demo)
                rag_pipeline.add_component("con_document_joiner_demo", con_document_joiner_demo)
                rag_pipeline.add_component("con_ranker_demo", con_ranker_demo)

                # 2. for demo-knowledge:
                # 2.1. for ground-truth demo knowledge:
                rag_pipeline.connect("grd_demo_embedder", "grd_embedding_retriever_demo")
                rag_pipeline.connect("grd_embedding_retriever_demo", "grd_document_joiner_demo")
                rag_pipeline.connect("grd_keyword_retriever_demo", "grd_document_joiner_demo")
                rag_pipeline.connect("grd_document_joiner_demo", "grd_ranker_demo")
                # 2.2. for contrast demo knowledge:
                rag_pipeline.connect("con_demo_embedder", "con_embedding_retriever_demo")
                rag_pipeline.connect("con_embedding_retriever_demo", "con_document_joiner_demo")
                rag_pipeline.connect("con_keyword_retriever_demo", "con_document_joiner_demo")
                rag_pipeline.connect("con_document_joiner_demo", "con_ranker_demo")
                # rag_pipeline.draw("retriver_pipeline2.png")
                # print("draw1 done")        
                content4retrieval_grd_demo = None
                content4retrieval_con_demo = None
                rag_pipeline.connect("grd_ranker_demo", "prompt_builder.grd_demo")
                rag_pipeline.connect("con_ranker_demo", "prompt_builder.con_demo")

                run_kwargs["grd_demo_embedder"] = {"text": content4retrieval_grd_demo} # type: ignore
                run_kwargs["con_demo_embedder"] = {"text": content4retrieval_con_demo} # type: ignore
                run_kwargs["grd_embedding_retriever_demo"] = { # type: ignore
                    "filters": {
                        "field": "meta.label",
                        "operator": "in",
                        "value": [grd]
                    },
                    "top_k": 1,
                }
                run_kwargs["con_embedding_retriever_demo"] = { # type: ignore
                    "filters": {
                        "field": "meta.label",
                        "operator": "in",
                        "value": [con]
                    }
                }
                run_kwargs["grd_keyword_retriever_demo"] = { # type: ignore
                    "query": content4retrieval_grd_demo,
                    "top_k": 1,
                    "filters": {
                        "field": "meta.label",
                        "operator": "in",
                        "value": [grd],
                    },
                }
                run_kwargs["con_keyword_retriever_demo"] = { # type: ignore
                    "query": content4retrieval_con_demo,
                    "top_k": 1,
                    "filters": {
                        "field": "meta.label",
                        "operator": "in",
                        "value": [con],
                    },
                }
                run_kwargs["grd_ranker_demo"] = { # type: ignore
                    "query": content4retrieval_grd_demo,
                    "top_k": 1,
                }
                run_kwargs["con_ranker_demo"] = { # type: ignore
                    "query": content4retrieval_con_demo,
                    "top_k": 1,
                }
             
            if args.debug:
                # pdb.set_trace()
                
                final_prompt = rag_pipeline.run(run_kwargs)
                print(f"final_prompt is:\n{final_prompt['prompt_builder']['prompt']}")
                assert(0)
            
            rag_pipeline.add_component("llm", generator) # type: ignore
            rag_pipeline.connect("prompt_builder", "llm")
            # rag_pipeline.draw("rag_pipeline.png")
    
            result = rag_pipeline.run(
                run_kwargs
            )
            an = result["llm"]["replies"][0]
            print(an)
            if i == 1:
                f.write(f'\nconfig={config}\n=================BEGIN A NEW RUN({grd})====================\n\n')
            f.write(an)
            f.write(f'\n{i} done_____________________________\n')
            ans.append(an)
            # assert(0)
            if i % 5 == 0:
                print(f"第{i}次预测完成")
    
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"总共耗时{elapsed_time}秒")
    # print(eval_generated_ans(ans, ground_ans, contrast_ans)

