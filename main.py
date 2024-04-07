from imports import *
from utils import read_raw_data_and_preprocess, filter_data_dict_with_var, get_openAI_model, gen_prompt_template_without_rag, eval_generated_ans, prepare_and_embed_documents, gen_prompt_template_with_rag, set_openAI_key_and_base, pretty_print_res_of_ranker, write_demo_knowledge,eval_by_gpt, read_multicls_data_and_preprocess


def chat_with_openai(data_dict, ground_ans: str="WALKING", contrast_ans: str="STANDING", answer_num: int=10, api_base: bool=True, model: str=MODEL["gpt3.5"], retrive=False, print_prompt=True):
    """
    return:
    results: list of str
    """
    results = []
    client = get_openAI_model(api_base, model)
    for i in range(answer_num):
        prompt = gen_prompt_template_without_rag(data_dict, ground_ans, contrast_ans, i, retrive)
        if print_prompt:
            print(prompt)
            return 
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        result = completion.choices[0].message.content
        if i % 5 == 0:
            print(f"第{i}次预测完成")
        results.append(result)
        print(result)
        print("-"*100)
    return results
        


if __name__ == "__main__":
    # data_dict = read_raw_data_and_preprocess()
    labels = np.loadtxt("/home/ant/RAG/data/IMU/smartphone+based+recognition+of+human+activities+and+postural+transitions/RawData/labels.txt", dtype=int)

    data_dict = read_multicls_data_and_preprocess(labels, sample_step=45)
    # filtered_data_dict = filter_data_dict_with_var(data_dict, thred=0.5, filter_by="body_acc", print_log=False)
    # data_dict = filtered_data_dict
    # demo_file_paths = write_demo_knowledge("/home/ant/RAG/IMU_knowledge/demo-knowledge", data_dict)
    # assert(0)
    # meta_data = [
    #     {
    #         "label": file_path.split("/")[-1][len("demo-knowledge"):-len("_i.txt")]
    #     }
    #     for file_path in demo_file_paths
    # ]
    # print(meta_data)
    # assert(0)
    candidates = ["LAYING", "WALKING_UPSTAIRS", "LIE_TO_SIT"]
    ground_ans = candidates[2]
    # contrast_ans = ["STANDING"]
    # candidates = [ground_ans] + contrast_ans
    start_time = time.perf_counter()
    # without retrieval:
    # ans = chat_with_openai(data_dict, ground_ans=ground_ans, contrast_ans=contrast_ans, answer_num=10, api_base=True, model=MODEL["gpt3.5"], retrive=False, print_prompt=False)
    # print(eval_generated_ans(ans, ground_ans, contrast_ans))

    # with retrieval:
    # 首先，准备好document_store并写入:
    KB_paths = [
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Accelemeters.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Acceleration.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Activity-recognition.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Angular-Velocity.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Gyroscope.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/How-work.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Human Activity Recognition using Accelerometer.pdf",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/knowledge-from-model.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Activity Recognition Using Cell Phone Acceleromete.pdf",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Patterns of Bipedal Walking on Tri-axial Accelerat.pdf",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Sitting.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Standing.txt",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/Uni- and triaxial accelerometric signals agree during daily routine, but show differences between sports.pdf",
        "/home/ant/RAG/IMU_knowledge/domain-knowledge/walking.txt",
    ]
    # Demo_paths = demo_file_paths
    # Demo_paths2 = demo_file_paths
    
    device = "cuda:0"
    # pdb.set_trace()
    document_store_domain = InMemoryDocumentStore()   
    splitter_kwags_domain = {"split_by": "sentence", "split_length": 2}
    embedded_document_store_KB = prepare_and_embed_documents(document_store_domain, KB_paths, draw=None, device=device, splitter_kwards=splitter_kwags_domain)

    document_store_demo = InMemoryDocumentStore()
    splitter_kwags_demo = {"split_by": "passage", "split_length": 1}
    # embedded_document_store_DM = prepare_and_embed_documents(document_store_demo, Demo_paths, draw=None, device=device, splitter_kwards=splitter_kwags_demo, meta_data=meta_data)

    # document_store_demo2 = InMemoryDocumentStore()
    # embedded_document_store_DM2 = prepare_and_embed_documents(document_store_demo2, Demo_paths2, draw="demo_indexing_pipeline.png", device=device, splitter_kwards=splitter_kwags_demo)



    
    ans = []
    with open("output_details.log", "a") as f:
        for i in range(10):
            # 建立一个rag的pipeline，使用hybrid的retrieval方法进行检索
            # first, 定义components:
            text_embedder = SentenceTransformersTextEmbedder(model=EMBEDDER_MODEL_LOCAL, device=ComponentDevice.from_str(device))
            grd_demo_embedder = SentenceTransformersTextEmbedder(model=EMBEDDER_MODEL_LOCAL, device=ComponentDevice.from_str(device))
            con_demo_embedder = SentenceTransformersTextEmbedder(model=EMBEDDER_MODEL_LOCAL, device=ComponentDevice.from_str(device))

            embedding_retriever_domain = InMemoryEmbeddingRetriever(embedded_document_store_KB)
            # grd_embedding_retriever_demo = InMemoryEmbeddingRetriever(embedded_document_store_DM)
            # con_embedding_retriever_demo = InMemoryEmbeddingRetriever(embedded_document_store_DM)

            keyword_retriever_domain = InMemoryBM25Retriever(embedded_document_store_KB)
            # grd_keyword_retriever_demo = InMemoryBM25Retriever(embedded_document_store_DM)
            # con_keyword_retriever_demo = InMemoryBM25Retriever(embedded_document_store_DM)

            document_joiner_domain = DocumentJoiner()
            grd_document_joiner_demo = DocumentJoiner()
            con_document_joiner_demo = DocumentJoiner()


            ranker_domain = TransformersSimilarityRanker(model=RANKER_MODEL_LOCAL)
            grd_ranker_demo = TransformersSimilarityRanker(model=RANKER_MODEL_LOCAL)
            con_ranker_demo = TransformersSimilarityRanker(model=RANKER_MODEL_LOCAL)
            template, data_des = gen_prompt_template_with_rag(data_dict, ground_ans, candidates, i) 
            prompt_builder = PromptBuilder(template=template)
            set_openAI_key_and_base(False, set_proxy=PROXY)
            generator = OpenAIGenerator(model=MODEL["gpt4"])

            # seconde: 创建pipeline:
            rag_pipeline = Pipeline()
            # 1. for domain-knowledge:
            rag_pipeline.add_component("text_embedder_domain", text_embedder)
            rag_pipeline.add_component("embedding_retriever_domain", embedding_retriever_domain)
            rag_pipeline.add_component("keyword_retriever_domain", keyword_retriever_domain)
            rag_pipeline.add_component("document_joiner_domain", document_joiner_domain)
            rag_pipeline.add_component("ranker_domain", ranker_domain)
            # 2. for demo-knowledge:
            # 2.1 for ground-truth demo knowledge:
            # rag_pipeline.add_component("grd_demo_embedder", grd_demo_embedder)
            # rag_pipeline.add_component("grd_embedding_retriever_demo", grd_embedding_retriever_demo)
            # rag_pipeline.add_component("grd_keyword_retriever_demo", grd_keyword_retriever_demo)
            # rag_pipeline.add_component("grd_document_joiner_demo", grd_document_joiner_demo)
            # rag_pipeline.add_component("grd_ranker_demo", grd_ranker_demo)
            # # 2.2 for contrast demo knowledge:
            # rag_pipeline.add_component("con_demo_embedder", con_demo_embedder)
            # rag_pipeline.add_component("con_embedding_retriever_demo", con_embedding_retriever_demo)
            # rag_pipeline.add_component("con_keyword_retriever_demo", con_keyword_retriever_demo)
            # rag_pipeline.add_component("con_document_joiner_demo", con_document_joiner_demo)
            # rag_pipeline.add_component("con_ranker_demo", con_ranker_demo)
            
            # third: 将components连接起来
            # 1. for domain-knowledge:
            rag_pipeline.connect("text_embedder_domain", "embedding_retriever_domain")
            rag_pipeline.connect("embedding_retriever_domain", "document_joiner_domain")
            rag_pipeline.connect("keyword_retriever_domain", "document_joiner_domain")
            rag_pipeline.connect("document_joiner_domain", "ranker_domain")
            # # 2. for demo-knowledge:
            # # 2.1. for ground-truth demo knowledge:
            # rag_pipeline.connect("grd_demo_embedder", "grd_embedding_retriever_demo")
            # rag_pipeline.connect("grd_embedding_retriever_demo", "grd_document_joiner_demo")
            # rag_pipeline.connect("grd_keyword_retriever_demo", "grd_document_joiner_demo")
            # rag_pipeline.connect("grd_document_joiner_demo", "grd_ranker_demo")
            # # 2.2. for contrast demo knowledge:
            # rag_pipeline.connect("con_demo_embedder", "con_embedding_retriever_demo")
            # rag_pipeline.connect("con_embedding_retriever_demo", "con_document_joiner_demo")
            # rag_pipeline.connect("con_keyword_retriever_demo", "con_document_joiner_demo")
            # rag_pipeline.connect("con_document_joiner_demo", "con_ranker_demo")
            # rag_pipeline.draw("retriver_pipeline2.png")
            # print("draw1 done")
            # query = f"""Based on the given data, choose the activity that the subject is most likely to be performing from the following two options: """
            candidates_str = ", ".join(candidates)
            query = f"The person’s action belongs to one of the following categories: [{candidates_str}]. Could you please tell me what action the person was doing based on the given information and IMU readings?"
            content4retrieval_domain = query + "\n" + """1. Triaxial acceleration signal: 
        The provided three-axis acceleration signals contain acceleration data for the X-axis, Y-axis, and Z-axis respectively. Each axis's data is a time-series signal consisting of multiple data samples, measured at a fixed time interval with a frequency of 10Hz(10 samples is collected per second). The unit is gravitational acceleration (g), equivalent to 9.8m/s^2. It's important to note that the measured acceleration is influenced by gravity, meaning the acceleration measurement along a certain axis will be affected by the vertical downward force of gravity. 
        2. Triaxial angular velocity signal: 
        The provided three-axis angular velocity signals contain angular velocity data for the X-axis, Y-axis, and Z-axis respectively. Each axis's data is a time-series signal consisting of multiple data samples, measured at a fixed time interval with a frequency of 10Hz. The unit is radians per second (rad/s).

        You need to comprehensively analyze the acceleration and angular velocity data on each axis. For each axis, you should analyze not only the magnitude and direction of each sampled data (the direction is determined by the positive or negative sign in the data) but also the changes and fluctuations in the sequential data along that axis. This analysis helps in understanding the subject's motion status. 
        For example, when the signal consistently shows significant fluctuations, it indicates that the person may be engaged in continuous activities, such as WALKING. On the other hand, when the signal consistently displays fewer fluctuations, it suggests that the person may be in a relatively calm state, such as STANDING. However, if there are differing patterns between segments of the signal sequence, and there are notable changes, particularly on certain axes during specific periods, it suggests that the person may be transitioning between activity states, such as in the case of LIE-TO-SIT"""
            content4retrieval_grd_demo = data_des 
            # content4retrieval_con_demo = f"ANSWER: {contrast_ans}"
            # retrieved = rag_pipeline.run(
            #     {
            #         # "text_embedder_domain": {"text": content4retrieval_domain},
            #         "grd_demo_embedder": {"text": content4retrieval_grd_demo},
            #         "con_demo_embedder": {"text": content4retrieval_con_demo},

            #         "grd_embedding_retriever_demo": {
            #             "filters": {
            #                 "field": "meta.label",
            #                 "operator": "in",
            #                 "value": [ground_ans]
            #             },
            #             "top_k": 2,
            #         },
            #         "con_embedding_retriever_demo": {
            #             "filters": {
            #                 "field": "meta.label",
            #                 "operator": "in",
            #                 "value": [contrast_ans]
            #             }
            #         },
            #         # "con_demo_embedder": {"text": content4retrieval_domain},
            #         # "keyword_retriever_domain": {"query": content4retrieval_grd_demo},
            #         "grd_keyword_retriever_demo": {"query": content4retrieval_grd_demo, "top_k": 1,
                                                
            #         "filters": {"field" : "meta.label", "operator": "in", "value": [ground_ans]
            #         }
            #         },
            #         "con_keyword_retriever_demo": {
            #             "query": content4retrieval_con_demo,
            #             "top_k": 1,
            #             "filters": {
            #                 "field": "meta.label",
            #                 "operator": "in",
            #                 "value": [contrast_ans],
            #             },
            #         },
            #         # "con_keyword_retriever_demo": {"query": content4retrieval_domain},
            #         # "ranker_domain": {"query": content4retrieval_domain},
            #         "grd_ranker_demo": {"query": content4retrieval_grd_demo, "top_k": 1},
            #         "con_ranker_demo": {"query": content4retrieval_con_demo, "top_k": 1},
            #     }
            # )
            # pretty_print_res_of_ranker(retrieved["ranker_domain"])
            # print("___________________________________________________________")
            # pretty_print_res_of_ranker(retrieved["grd_ranker_demo"])
            # print("___________________________________________________________")
            # assert(0)
            # pretty_print_res_of_ranker(retrieved["con_ranker_demo"])
            # assert(0)
            rag_pipeline.add_component("prompt_builder", prompt_builder)
            rag_pipeline.connect("ranker_domain", "prompt_builder.documents_domain")
            # rag_pipeline.connect("grd_ranker_demo", "prompt_builder.grd_demo")
            # rag_pipeline.connect("con_ranker_demo", "prompt_builder.con_demo")
            # rag_pipeline.connect("con_ranker_demo", "prompt_builder.document_demo_con")
            # 打印看看喂给llm的prompt长什么样子
            # final_prompt = rag_pipeline.run(
            #     {
            #         "text_embedder_domain": {"text": content4retrieval_domain},
            #         "keyword_retriever_domain": {"query": content4retrieval_domain},
            #         "ranker_domain": {"query": content4retrieval_domain},
            #         # "grd_demo_embedder": {"text": content4retrieval_grd_demo},
            #         # "con_demo_embedder": {"text": content4retrieval_con_demo},
            #         # "grd_embedding_retriever_demo": {
            #         #     "filters": {
            #         #         "field": "meta.label",
            #         #         "operator": "in",
            #         #         "value": [ground_ans],
            #         #     },
            #         #     "top_k": 1,
            #         # },
            #         # "con_embedding_retriever_demo": {
            #         #     "filters": {
            #         #         "field": "meta.label",
            #         #         "operator": "in",
            #         #         "value": [contrast_ans],
            #         #     }
            #         # },
            #         # "grd_keyword_retriever_demo": {
            #         #     "query": content4retrieval_grd_demo,
            #         #     "top_k": 1,
            #         #     "filters": {
            #         #         "field": "meta.label",
            #         #         "operator": "in",
            #         #         "value": [ground_ans],
            #         #     },
            #         # },
            #         # "con_keyword_retriever_demo": {
            #         #     "query": content4retrieval_con_demo,
            #         #     "top_k": 1,
            #         #     "filters": {
            #         #         "field": "meta.label",
            #         #         "operator": "in",
            #         #         "value": [contrast_ans],
            #         #     },
            #         # },
            #         # "grd_ranker_demo": {
            #         #     "query": content4retrieval_grd_demo,
            #         #     "top_k": 1,
            #         # },
            #         # "con_ranker_demo": {
            #         #     "query": content4retrieval_con_demo,
            #         #     "top_k": 1,
            #         # },             
            #         "prompt_builder": {"query": query},
            #     }
            # )
            # print(f"final_prompt is:\n{final_prompt['prompt_builder']['prompt']}")
            # print("___________________________________________________________")
            # assert(0)
            rag_pipeline.add_component("llm", generator)
            rag_pipeline.connect("prompt_builder", "llm")
            # rag_pipeline.draw("rag_pipeline.png")
            result = rag_pipeline.run(
                {
                    "text_embedder_domain": {"text": content4retrieval_domain},
                    "keyword_retriever_domain": {"query": content4retrieval_domain},
                    "ranker_domain": {"query": content4retrieval_domain},
                    # "grd_demo_embedder": {"text": content4retrieval_grd_demo},
                    # "con_demo_embedder": {"text": content4retrieval_con_demo},
                    # "grd_embedding_retriever_demo": {
                    #     "filters": {
                    #         "field": "meta.label",
                    #         "operator": "in",
                    #         "value": [ground_ans],
                    #     },
                    #     "top_k": 1,
                    # },
                    # "con_embedding_retriever_demo": {
                    #     "filters": {
                    #         "field": "meta.label",
                    #         "operator": "in",
                    #         "value": [contrast_ans],
                    #     }
                    # },
                    # "grd_keyword_retriever_demo": {
                    #     "query": content4retrieval_grd_demo,
                    #     "top_k": 1,
                    #     "filters": {
                    #         "field": "meta.label",
                    #         "operator": "in",
                    #         "value": [ground_ans],
                    #     },
                    # },
                    # "con_keyword_retriever_demo": {
                    #     "query": content4retrieval_con_demo,
                    #     "top_k": 1,
                    #     "filters": {
                    #         "field": "meta.label",
                    #         "operator": "in",
                    #         "value": [contrast_ans],
                    #     },
                    # },
                    # "grd_ranker_demo": {
                    #     "query": content4retrieval_grd_demo,
                    #     "top_k": 1,
                    # },
                    # "con_ranker_demo": {
                    #     "query": content4retrieval_con_demo,
                    #     "top_k": 1,
                    # },             
                    "prompt_builder": {"query": query},
                }
            )
            an = result["llm"]["replies"][0]
            print(an)
            if i == 0:
                f.write('=================BEGIN A NEW RUN====================\n\n')
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
   
    # print(eval_by_gpt(ans, candidates, ground_ans, None))
    with open('output_details.txt', 'w') as f:
        for an in ans:
            f.write(an)
            f.write("_____________________________\n\n")

    






    
 