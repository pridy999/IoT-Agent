from imports import *


def gen_content4retrive_domain(task_type, data_des=""):
    return content4retrieve_domain[task_type] + data_des 
def Role_Definition(args):
    """input: Task_Descriping(str), Preprocessed_Data(str), model(str)
    output: role_definition(str)"""
    return Role_des[args.task_type]

def Role_Definition_llama(args):
    """input: Task_Descriping(str), Preprocessed_Data(str), model(str)
    output: role_definition(str)"""
    return Role_des_llama[args.task_type]

def gen_prompt_with_rag_ECG(args, data_dict, is_Pos=True, i: int=1):
    N_signals = data_dict["N_signals"][-i]
    V_signals = data_dict["V_signals"][-i]
    N_signals_str = ", ".join([f"{x[0]}mV" for x in N_signals])
    V_signals_str = ", ".join([f"{x[0]}mV" for x in V_signals])
    N_signals_demo = data_dict["N_signals"][-i-1]
    V_signals_demo = data_dict["V_signals"][-i-1]
    N_signals_demo_str = ", ".join([f"{x[0]}mV" for x in N_signals_demo])
    V_signals_demo_str = ", ".join([f"{x[0]}mV" for x in V_signals_demo])

    # print(N_signals_str)
    prompt = f"""{Role_Definition(args)}

ECG DATA:
The ECG data is collected from a patient's heart. The data consists of a series of electrical signals that represent the heart's electrical activity. The signals are measured in millivolts (mV) and are recorded over a period of time at the sampling frequency of 60Hz. This means there is an interval of 0.017 seconds between the two voltage values.  The data is divided into two categories: normal heartbeats (N) and ventricular ectopic beats (V). The normal heartbeats represent the regular electrical activity of the heart, while the ventricular ectopic beats represent abnormal electrical activity. The data is collected using a single-channel ECG device."""
    prompt += """
EXPERT:
{% for domain_doc in documents_domain %}
    {{ domain_doc.content }}
{% endfor %}

"You can analyze whether the heartbeat is normal by considering a combination of factors such as the amplitude of peaks or valleys appearing in the electrocardiogram (ECG) time series, the time intervals between adjacent peaks or valleys, and the fluctuations in voltage values within the ECG data."
"""
    prompt += f"""
EXAMPLE1:
THE GIVEN ECG DATA:
{N_signals_str}
ANSWER: Normal heartbeat (N)

EXAMPLE2:
THE GIVEN ECG DATA:
{V_signals_str}
ANSWER: Premature ventricular contraction (V)
"""
    prompt += """
QUESTION: {{ query }}"""
    if is_Pos:
        data_des = f"""
THE GIVEN ECG DATA:
{N_signals_demo_str}
"""
        prompt += data_des
    else:
        data_des = f"""
THE GIVEN ECG DATA:
{V_signals_demo_str}
"""
        prompt += data_des
    prompt += """
Please analyze the data step by step to explain what it reflects, and then provide your final answer based on your analysis: "Is it a Normal heartbeat(N) or Premature ventricular contraction beat(V)?"
ANALYSIS:
ANSWER:
"""
    return prompt, data_des
def gen_prompt_template_with_rag_imu_2cls(args, label2ids, data_dict, ground_ans: str="WALKING", contract_ans: str="STANDING", i: int=0): 

    def create_data_des(i, is_ground=True):
        if is_ground:
            target_cls = ground_ans 
        else:
            target_cls = contract_ans
        acc_x = data_dict[label2ids[target_cls]]["total_acc"][i][0]
        acc_y = data_dict[label2ids[target_cls]]["total_acc"][i][1]
        acc_z = data_dict[label2ids[target_cls]]["total_acc"][i][2]
        gyr_x = data_dict[label2ids[target_cls]]["body_gyro"][i][0]
        gyr_y = data_dict[label2ids[target_cls]]["body_gyro"][i][1]
        gyr_z = data_dict[label2ids[target_cls]]["body_gyro"][i][2] 
        acc_x_str = ", ".join([f"{x}g" for x in acc_x])
        acc_y_str = ", ".join([f"{x}g" for x in acc_y])
        acc_z_str = ", ".join([f"{x}g" for x in acc_z])
        gyr_x_str = ", ".join([f"{x}rad/s" for x in gyr_x])
        gyr_y_str = ", ".join([f"{x}rad/s" for x in gyr_y])
        gyr_z_str = ", ".join([f"{x}rad/s" for x in gyr_z])
        data_des = f"""
1. Triaxial acceleration signal: 
X-axis: {acc_x_str} 
Y-axis: {acc_y_str} 
Z-axis: {acc_z_str} 
X-axis-mean={np.around(np.mean(acc_x), 3)}g, X-axis-var={np.around(np.var(acc_x), 3)} 
Y-axis-mean={np.around(np.mean(acc_y), 3)}g, Y-axis-var={np.around(np.var(acc_y), 3)} 
Z-axis-mean={np.around(np.mean(acc_z), 3)}g, Z-axis-var={np.around(np.var(acc_z), 3)} 
2. Triaxial angular velocity signal: 
X-axis: {gyr_x_str} 
Y-axis: {gyr_y_str} 
Z-axis: {gyr_z_str} 
X-axis-mean={np.around(np.mean(gyr_x), 3)}rad/s, X-axis-var={np.around(np.var(gyr_x), 3)} 
Y-axis-mean={np.around(np.mean(gyr_y), 3)}rad/s, Y-axis-var={np.around(np.var(gyr_y), 3)} 
Z-axis-mean={np.around(np.mean(gyr_z), 3)}rad/s, Z-axis-var={np.around(np.var(gyr_z), 3)}"""
        return data_des
    data_des = create_data_des(i)
    demo_grd_data_des = create_data_des(i+1)
    demo_con_data_des = create_data_des(i, is_ground=False)
    prompt = f"""{Role_Definition(args)}

EXPERT:
1. Triaxial acceleration signal: 
The provided three-axis acceleration signals contain acceleration data for the X-axis, Y-axis, and Z-axis respectively. Each axis's data is a time-series signal consisting of some data samples, measured at a fixed time interval with a frequency of 10Hz(10 samples is collected per second). The unit is gravitational acceleration (g), equivalent to 9.8m/s^2. It's important to note that the measured acceleration is influenced by gravity, meaning the acceleration measurement along a certain axis will be affected by the vertical downward force of gravity. 
2. Triaxial angular velocity signal: 
The provided three-axis angular velocity signals contain angular velocity data for the X-axis, Y-axis, and Z-axis respectively. Each axis's data is a time-series signal consisting of some data samples, measured at a fixed time interval with a frequency of 10Hz. The unit is radians per second (rad/s).
3. Other domain knowledge:
"""
    prompt += """
{% for domain_doc in documents_domain %}{{ domain_doc.content }}{% endfor %}
"""
    prompt += f"""
EXAMPLE1:
{demo_grd_data_des}
"""
    prompt += """QUESTION:
{{ query }}
"""
    prompt += f"""[{ground_ans}, {contract_ans}]
ANSWER: {ground_ans}

EXAMPLE2:
{demo_con_data_des}
"""
    prompt += """QUESTION:
{{ query }}
"""
    prompt += f"""[{ground_ans}, {contract_ans}]
ANSWER: {contract_ans}


"""

    prompt += """

You need to comprehensively analyze the acceleration and angular velocity data on each axis. For each axis, you should analyze not only the magnitude and direction of each sampled data (the direction is determined by the positive or negative sign in the data) but also the changes and fluctuations in the sequential data along that axis. This analysis helps in understanding the subject's motion status.

"""
    prompt += f"""
Before answering your question, you must refer to the EXPERT and EXAMPLES above and make analysis step by step.
​
THE GIVEN DATA: 
{data_des}
"""
    prompt += """QUESTION:
{{ query }}
"""
    prompt += f"""[{ground_ans}, {contract_ans}]
ANALYSIS:
ANSWER:
"""
    return prompt, data_des

# EXAMPLE1:
# {% for d in grd_demo %}{{ d.content }}{% endfor %}

# EXAMPLE2:
# {% for d in con_demo %}{{ d.content }}{% endfor %}

#  to the previous EXAMPLES and compare the signal data, the mean data, and the var data in the EXAMPLES with those in the question,
# EXAMPLE1:
# {{ document_demo_grd.content }}
# EXAMPLE2:
# {{ document_demo_con.content }}
#     return """
# Given the following information, answer the question.

# Context:
# {% for document in documents %}
#     {{ document.content }}
# {% endfor %}

# Question: {{question}}
# Answer:
# """

def gen_prompt_tamplate_with_rag_machine(args, data_dict, label_dict, target, i: int=0, ground_truth="Pos"):
    assert target in label_dict.keys()
    if target == "Cooler condition %":
        Cooler_condition_3_data = {}
        Cooler_condition_100_data = {}
        for key in data_dict.keys():
            Cooler_condition_3_data[key] = data_dict[key][np.where(label_dict["Cooler condition %"] == 3)]
            Cooler_condition_100_data[key] = data_dict[key][np.where(label_dict["Cooler condition %"] == 100)]
        print(f"Cooler_condition_3_data: {Cooler_condition_3_data['PS1'].shape}")
        print(f"Cooler_condition_100_data: {Cooler_condition_100_data['PS1'].shape}")
        TS_neg_demo = Cooler_condition_3_data["TS1"][-i-1]
        CP_neg_demo = Cooler_condition_3_data["CP"][-i-1]
        CE_neg_demo = Cooler_condition_3_data["CE"][-i-1]
        TS_pos_demo = Cooler_condition_100_data["TS1"][-i-1]
        CP_pos_demo = Cooler_condition_100_data["CP"][-i-1]
        CE_pos_demo = Cooler_condition_100_data["CE"][-i-1]
        TS_pos_demo_str = ", ".join([f"{x}°C" for x in TS_pos_demo])
        CP_pos_demo_str = ", ".join([f"{x}KW" for x in CP_pos_demo])
        CE_pos_demo_str = ", ".join([f"{x}%" for x in CE_pos_demo])
        TS_neg_demo_str = ", ".join([f"{x}°C" for x in TS_neg_demo])
        CP_neg_demo_str = ", ".join([f"{x}KW" for x in CP_neg_demo])
        CE_neg_demo_str = ", ".join([f"{x}%" for x in CE_neg_demo])

        TS_pos = Cooler_condition_100_data["TS1"][-i]
        CP_pos = Cooler_condition_100_data["CP"][-i]
        CE_pos = Cooler_condition_100_data["CE"][-i]
        TS_neg = Cooler_condition_3_data["TS1"][-i]
        CP_neg = Cooler_condition_3_data["CP"][-i]
        CE_neg = Cooler_condition_3_data["CE"][-i]
        Ts_pos_str = ", ".join([f"{x}°C" for x in TS_pos])
        CP_pos_str = ", ".join([f"{x}KW" for x in CP_pos])
        CE_pos_str = ", ".join([f"{x}%" for x in CE_pos])
        TS_neg_str = ", ".join([f"{x}°C" for x in TS_neg])
        CP_neg_str = ", ".join([f"{x}KW" for x in CP_neg])
        CE_neg_str = ", ".join([f"{x}%" for x in CE_neg])
        prompt = f"""{Role_Definition(args)}

SENSOR DATA:
For each sensor, we collected 60 data points over a period of 60 seconds at a monitoring frequency of 1Hz (measuring sensor data once every second), forming a time series of length 60. We measured the following sequences using temperature sensors, Cooling power sensors, and Cooling efficiency sensors:

1. **Temperature Change Sequence**: Reflects the machine's temperature variation over 60 seconds, in degrees Celsius. By analyzing this sequence, you can assess whether the cooling equipment is operating normally. Typically, when the cooling system is functioning well, the machine's temperature is relatively low and does not fluctuate too significantly. If the temperature consistently remains at a high degrees Celsius or fluctuates significantly, it may indicate an abnormal issue with the cooling equipment.

2. **Cooling Power Change Sequence**: Reflects the variation in the cooling power of the machine's cooling equipment over 60 seconds, in kilowatts (KW). By analyzing this sequence, you can determine if the cooling equipment is operating normally. Generally, when the cooling system is functioning properly, the cooling power is relatively high and remains relatively stable throughout the period. If the power consistently stays low, it may suggest an abnormal issue with the cooling equipment.

3. **Cooling Efficiency Change Sequence**: Reflects the variation in the efficiency of the machine's cooling equipment over 60 seconds, in percentage (%). By analyzing this sequence, you can judge if the cooling equipment is operating normally. Typically, when the cooling system is working well, the cooling efficiency is relatively high, otherwise, it indicates that there may be an abnormal issue with the cooling equipment."""
        if not args.no_domain_knowledge:
            prompt += """
EXPERT: 
{% for domain_doc in documents_domain %}
    {{ domain_doc.content }}
{% endfor %}



"""     

        prompt += f"""
EXAMPLE1:
1. Temperature Change Sequence:
{TS_neg_demo_str}
2. Cooling Power Change Sequence:
{CP_neg_demo_str}
3. Cooling Efficiency Change Sequence:
{CE_neg_demo_str}
ANSWER: not operating normally. 
EXAMPLE2:
1. Temperature Change Sequence:
{TS_pos_demo_str}
2. Cooling Power Change Sequence:
{CP_pos_demo_str}
3. Cooling Efficiency Change Sequence:
{CE_pos_demo_str}
ANSWER: operating normally."""
        prompt += """
QUESTION: {{ query }}"""
        if ground_truth == "Pos":
            data_des = f"""
THE GIVEN DATA:
1. Temperature Change Sequence:
{Ts_pos_str}
2. Cooling Power Change Sequence:
{CP_pos_str}
3. Cooling Efficiency Change Sequence:
{CE_pos_str}
"""
            prompt += data_des
        else:
            data_des = f"""
THE GIVEN DATA:
1. Temperature Change Sequence:
{TS_neg_str}
2. Cooling Power Change Sequence:
{CP_neg_str}
3. Cooling Efficiency Change Sequence:
{CE_neg_str}
"""
            prompt += data_des
        prompt += """
Please analyze the data step by step to explain what it reflects, and then provide your final answer based on your analysis: "Is the machine's cooling system functioning properly?"
ANALYSIS:
ANSWER:
"""
    elif target == "":
        pass 
    return prompt, data_des




# def prompt_template_generation(Task_Description, Preprocessed_Data):
#     """template中的变量为：domain_ks, demonstrations, question"""
#     Role_definition = Role_Definition(Task_Description, Preprocessed_Data)
#     base_template = f"""{Role_definition}.\n The following data has been collected from the devices worn by the subjects:\n {Preprocessed_Data}.\n When answering questions, you can refer to the knowledge of the experts below, as well as some demonstrations:\n\n Experts: """
#     domain_knowledge = """
#     {% for domain_k in domain_ks %}
#         {{ domain_ks.content }}
#     {% endfor %}"""
#     demonstrations = """
#     {% for demonstration in demonstrations %}
#         {{ demonstration.content }}
#     {% endfor %}"""
#     question = """Question: {{ question }}\nAnswer:"""
#     prompt_template = base_template + domain_knowledge + demonstrations + question 
#     return prompt_template


def gen_prompt_with_rag_wifi_occupancy(args, data_dict, ground_ans: str="no_person", contract_ans: str="have_person", i: int=0):
    csi = data_dict[ground_ans][i,:,:]
    no_person = data_dict['no_person']
    have_person = data_dict['have_person']
    a_n = np.mean(np.mean(no_person, axis=(1,2)))
    a_h = np.mean(np.mean(have_person, axis=(1,2)))

    b_n = np.mean(np.std(np.mean(no_person, axis=2),axis=1))
    b_h = np.mean(np.std(np.mean(have_person, axis=2), axis=1))

    d_n = np.mean(np.mean(np.std(no_person, axis=1),axis=1))
    d_h = np.mean(np.mean(np.std(have_person, axis=1), axis=1))
    data_des = f"""
    The mean value of CSI: {np.mean(csi)}
    The standard deviation across subcarriers for the mean CSI amplitude over time: {np.std(np.mean(csi, axis=1), axis=0)}
    The mean standard deviation across subcarriers for each time point: {np.mean(np.std(csi, axis=0))}
    """

    prompt = f"""{Role_Definition(args)}
    EXPERT:
    1. CSI data: 
    The structure of CSI data is {csi.shape}, where the first dimension means a time-series signal consisting of {csi.shape[0]} data samples and the second dimension means {csi.shape[1]} subcarriers of CSI data. It represents the amplitude of the signal, which can be reflected by the human presence.
    2. The mean value of CSI: 
    The mean value of CSI is a scalar that describe the average amplitude of the CSI data.
    3. The standard deviation across subcarriers for the mean CSI amplitude over time:
    It is a scalar which represents the variability of the mean CSI amplitude across different subcarriers over time.
    4. The mean std of CSI across the time axis:
    It is a scalar that describes the average std of CSI signals for each subcarrier over time. It reflects the overall degree of signal oscillation in time.
    5. The mean values for no_person and have_person classes:
    No_person: [The mean value of CSI: {a_n}. The standard deviation across subcarriers for the mean CSI amplitude over time: {b_n}. The mean standard deviation across subcarriers for each time point: {d_n}]
    Have_person: [The mean value of CSI: {a_h}. The standard deviation across subcarriers for the mean CSI amplitude over time: {b_h}. The mean standard deviation across subcarriers for each time point: {d_h}]
    """
    prompt += """
    {% for domain_doc in documents_domain %}
    {{ domain_doc.content }}
    {% endfor %}

    You need to comprehensively analyze the main value of CSI, the standard deviation across subcarriers for the mean CSI amplitude over time, and the mean std of CSI across the time axis. This analysis helps in understanding the presence of a person in the room.

    EXAMPLE1:
    {% for d in grd_demo %}{{ d.content }}{% endfor %}

    EXAMPLE2:
    {% for d in con_demo %}{{ d.content }}{% endfor %}

    QUESTION: {{ query }}
    """
    prompt += f"""
    {ground_ans}
    {contract_ans}
    THE GIVEN DATA: 
    {data_des}
    Before answering your question, you must refer to the provided knowledge and the previous examples and compare the mean data, the standard deviation across subcarriers for the mean CSI amplitude over time and the mean std of CSI across the time axis in the examples with those in the question comprehensively, in order to help you make a clear choice.
    Please analyze the data step by step to and provide your final answer based on your analysis:"Is there is a person or not?"
    You only need to give me the answer in the following format, without output any analysis details:
    [ANSWER]:
    """
    return prompt, data_des


def gen_prompt_with_rag_wifi_occupancy_llama(args, data_dict, ground_ans: str="no_person", contract_ans: str="have_person", i: int=0):
    csi = data_dict[ground_ans][i,:,:]
    no_person = data_dict['no_person']
    have_person = data_dict['have_person']
    a_n = np.mean(np.mean(no_person, axis=(1,2)))
    a_h = np.mean(np.mean(have_person, axis=(1,2)))

    b_n = np.mean(np.std(np.mean(no_person, axis=2),axis=1))
    b_h = np.mean(np.std(np.mean(have_person, axis=2), axis=1))

    d_n = np.mean(np.mean(np.std(no_person, axis=1),axis=1))
    d_h = np.mean(np.mean(np.std(have_person, axis=1), axis=1))
    data_des = f"""
    The mean value of CSI: {np.mean(csi)}
    The standard deviation across subcarriers for the mean CSI amplitude over time: {np.std(np.mean(csi, axis=1), axis=0)}
    The mean standard deviation across subcarriers for each time point: {np.mean(np.std(csi, axis=0))}
    """

    prompt = f"""{Role_Definition_llama(args)}
    EXPERT:
    1. CSI data: 
    The structure of CSI data is {csi.shape}, where the first dimension means a time-series signal consisting of {csi.shape[0]} data samples and the second dimension means {csi.shape[1]} subcarriers of CSI data. It represents the amplitude of the signal, which can be reflected by the human presence.
    2. The mean value of CSI: 
    The mean value of CSI is a scalar that describe the average amplitude of the CSI data.
    3. The standard deviation across subcarriers for the mean CSI amplitude over time:
    It is a scalar which represents the variability of the mean CSI amplitude across different subcarriers over time.
    4. The mean std of CSI across the time axis:
    It is a scalar that describes the average std of CSI signals for each subcarrier over time. It reflects the overall degree of signal oscillation in time.
    5. The mean values for no_person and have_person classes:
    No_person: [The mean value of CSI: {a_n}. The standard deviation across subcarriers for the mean CSI amplitude over time: {b_n}. The mean standard deviation across subcarriers for each time point: {d_n}]
    Have_person: [The mean value of CSI: {a_h}. The standard deviation across subcarriers for the mean CSI amplitude over time: {b_h}. The mean standard deviation across subcarriers for each time point: {d_h}]
    """
    prompt += """
    {% for domain_doc in documents_domain %}
    {{ domain_doc.content }}
    {% endfor %}

    You need to comprehensively analyze the main value of CSI, the standard deviation across subcarriers for the mean CSI amplitude over time, and the mean std of CSI across the time axis. This analysis helps in understanding the presence of a person in the room.

    EXAMPLE1:
    {% for d in grd_demo %}{{ d.content }}{% endfor %}

    EXAMPLE2:
    {% for d in con_demo %}{{ d.content }}{% endfor %}

    QUESTION: {{ query }}
    """
    prompt += f"""
    {ground_ans}
    {contract_ans}
    THE GIVEN DATA: 
    {data_des}
    Before answering your question, you must refer to the provided knowledge and the previous examples and compare the mean data, the standard deviation across subcarriers for the mean CSI amplitude over time and the mean std of CSI across the time axis in the examples with those in the question comprehensively, in order to help you make a clear choice.
    Please analyze the data step by step to and provide your final answer based on your analysis:"Is there is a person or not?"
    You only need to give me the answer in the following format, without output any analysis details:
    [ANSWER]:
    """
    return prompt, data_des


def gen_prompt_template_without_rag(data_dict, ground_ans: str="WALKING", contrast_ans: str="STANDING", i: int=0):
    # TODO
    acc_x = data_dict[label2ids[ground_ans]]["total_acc"][i][0]
    acc_y = data_dict[label2ids[ground_ans]]["total_acc"][i][1]
    acc_z = data_dict[label2ids[ground_ans]]["total_acc"][i][2]
    gyr_x = data_dict[label2ids[ground_ans]]["body_gyro"][i][0]
    gyr_y = data_dict[label2ids[ground_ans]]["body_gyro"][i][1]
    gyr_z = data_dict[label2ids[ground_ans]]["body_gyro"][i][2] 
    demo_grd_acc_x = data_dict[label2ids[ground_ans]]["total_acc"][i+1][0]
    demo_grd_acc_y = data_dict[label2ids[ground_ans]]["total_acc"][i+1][1]
    demo_grd_acc_z = data_dict[label2ids[ground_ans]]["total_acc"][i+1][2]
    demo_grd_gyr_x = data_dict[label2ids[ground_ans]]["body_gyro"][i+1][0]
    demo_grd_gyr_y = data_dict[label2ids[ground_ans]]["body_gyro"][i+1][1]
    demo_grd_gyr_z = data_dict[label2ids[ground_ans]]["body_gyro"][i+1][2]
    demo_con_acc_x = data_dict[label2ids[contrast_ans]]["total_acc"][i][0]
    demo_con_acc_y = data_dict[label2ids[contrast_ans]]["total_acc"][i][1]
    demo_con_acc_z = data_dict[label2ids[contrast_ans]]["total_acc"][i][2]
    demo_con_gyr_x = data_dict[label2ids[contrast_ans]]["body_gyro"][i][0]
    demo_con_gyr_y = data_dict[label2ids[contrast_ans]]["body_gyro"][i][1]
    demo_con_gyr_z = data_dict[label2ids[contrast_ans]]["body_gyro"][i][2]
    acc_x_str = ", ".join([f"{x}g" for x in acc_x])
    acc_y_str = ", ".join([f"{x}g" for x in acc_y])
    acc_z_str = ", ".join([f"{x}g" for x in acc_z])
    gyr_x_str = ", ".join([f"{x}rad/s" for x in gyr_x])
    gyr_y_str = ", ".join([f"{x}rad/s" for x in gyr_y])
    gyr_z_str = ", ".join([f"{x}rad/s" for x in gyr_z])
    demo_grd_acc_x_str = ", ".join([f"{x}g" for x in demo_grd_acc_x])
    demo_grd_acc_y_str = ", ".join([f"{x}g" for x in demo_grd_acc_y])
    demo_grd_acc_z_str = ", ".join([f"{x}g" for x in demo_grd_acc_z])
    demo_grd_gyr_x_str = ", ".join([f"{x}rad/s" for x in demo_grd_gyr_x])
    demo_grd_gyr_y_str = ", ".join([f"{x}rad/s" for x in demo_grd_gyr_y])
    demo_grd_gyr_z_str = ", ".join([f"{x}rad/s" for x in demo_grd_gyr_z])
    demo_con_acc_x_str = ", ".join([f"{x}g" for x in demo_con_acc_x])
    demo_con_acc_y_str = ", ".join([f"{x}g" for x in demo_con_acc_y])
    demo_con_acc_z_str = ", ".join([f"{x}g" for x in demo_con_acc_z])
    demo_con_gyr_x_str = ", ".join([f"{x}rad/s" for x in demo_con_gyr_x])
    demo_con_gyr_y_str = ", ".join([f"{x}rad/s" for x in demo_con_gyr_y])
    demo_con_gyr_z_str = ", ".join([f"{x}rad/s" for x in demo_con_gyr_z])
    prompt = f"""{Role_Definition()}

EXPERT: 
1. Triaxial acceleration signal: 
The provided three-axis acceleration signals contain acceleration data for the X-axis, Y-axis, and Z-axis respectively. Each axis's data is a time-series signal consisting of 26 data samples, measured at a fixed time interval with a frequency of 10Hz(10 samples is collected per second). The unit is gravitational acceleration (g), equivalent to 9.8m/s^2. It's important to note that the measured acceleration is influenced by gravity, meaning the acceleration measurement along a certain axis will be affected by the vertical downward force of gravity. 
2. Triaxial angular velocity signal: 
The provided three-axis angular velocity signals contain angular velocity data for the X-axis, Y-axis, and Z-axis respectively. Each axis's data is a time-series signal consisting of 26 data samples, measured at a fixed time interval with a frequency of 10Hz. The unit is radians per second (rad/s). 
​
You need to comprehensively analyze the acceleration and angular velocity data on each axis. For each axis, you should analyze not only the magnitude and direction of each sampled data (the direction is determined by the positive or negative sign in the data) but also the changes and fluctuations in the sequential data along that axis. This analysis helps in understanding the subject's motion status. For example, signals with greater fluctuations in sample data in the sequence often indicate the subject is engaging in more vigorous activities like WALKING, whereas signals with smaller fluctuations in sample data often indicate the subject is engaged in calmer activities like STANDING. 
​
EXAMPLE1: 
1. Triaxial acceleration signal: 
X-axis: {demo_grd_acc_x_str} 
Y-axis: {demo_grd_acc_y_str} 
Z-axis: {demo_grd_acc_z_str} 
X-axis-mean={np.around(np.mean(demo_grd_acc_x), 3)}, X-axis-var={np.around(np.var(demo_grd_acc_x), 3)} 
Y-axis-mean={np.around(np.mean(demo_grd_acc_y), 3)}, Y-axis-var={np.around(np.var(demo_grd_acc_y), 3)} 
Z-axis-mean={np.around(np.mean(demo_grd_acc_z), 3)}, Z-axis-var={np.around(np.var(demo_grd_acc_z), 3)} 
2. Triaxial angular velocity signal: 
X-axis: {demo_grd_gyr_x_str} 
Y-axis: {demo_grd_gyr_y_str} 
Z-axis: {demo_grd_gyr_z_str} 
X-axis-mean={np.around(np.mean(demo_grd_gyr_x), 3)}, X-axis-var={np.around(np.var(demo_grd_gyr_x), 3)} 
Y-axis-mean={np.around(np.mean(demo_grd_gyr_y), 3)}, Y-axis-var={np.around(np.var(demo_grd_gyr_y), 3)} 
Z-axis-mean={np.around(np.mean(demo_grd_gyr_z), 3)}, Z-axis-var={np.around(np.var(demo_grd_gyr_z), 3)} 
ANSWER: {ground_ans} 
​
EXAMPLE2: 
1. Triaxial acceleration signal: 
X-axis: {demo_con_acc_x_str} 
Y-axis: {demo_con_acc_y_str} 
Z-axis: {demo_con_acc_z_str} 
X-axis-mean={np.around(np.mean(demo_con_acc_x), 3)}, X-axis-var={np.around(np.var(demo_con_acc_x), 3)} 
Y-axis-mean={np.around(np.mean(demo_con_acc_y), 3)}, Y-axis-var={np.around(np.var(demo_con_acc_y), 3)} 
Z-axis-mean={np.around(np.mean(demo_con_acc_z), 3)}, Z-axis-var={np.around(np.var(demo_con_acc_z), 3)} 
2. Triaxial angular velocity signal: 
X-axis: {demo_con_gyr_x_str} 
Y-axis: {demo_con_gyr_y_str} 
Z-axis: {demo_con_gyr_z_str} 
X-axis-mean={np.around(np.mean(demo_con_gyr_x), 3)}, X-axis-var={np.around(np.var(demo_con_gyr_x), 3)} 
Y-axis-mean={np.around(np.mean(demo_con_gyr_y), 3)}, Y-axis-var={np.around(np.var(demo_con_gyr_y), 3)} 
Z-axis-mean={np.around(np.mean(demo_con_gyr_z), 3)}, Z-axis-var={np.around(np.var(demo_con_gyr_z), 3)} 
ANSWER: {contrast_ans} 
​
​
QUESTION: Based on the given data, choose the activity that the subject is most likely to be performing from the following two options: 
{ground_ans} 
{contrast_ans} 
Before answering your question, you must refer to the previous examples and compare the signal data, the mean data, and the var data in the examples with those in the question, in order to help you make a clear choice. 
​
​
THE GIVEN DATA: 
1. Triaxial acceleration signal: 
X-axis: {acc_x_str} 
Y-axis: {acc_y_str} 
Z-axis: {acc_z_str} 
X-axis-mean={np.around(np.mean(acc_x), 3)}, X-axis-var={np.around(np.var(acc_x), 3)} 
Y-axis-mean={np.around(np.mean(acc_y), 3)}, Y-axis-var={np.around(np.var(acc_y), 3)} 
Z-axis-mean={np.around(np.mean(acc_z), 3)}, Z-axis-var={np.around(np.var(acc_z), 3)} 
2. Triaxial angular velocity signal: 
X-axis: {gyr_x_str} 
Y-axis: {gyr_y_str} 
Z-axis: {gyr_z_str} 
X-axis-mean={np.around(np.mean(gyr_x), 3)}, X-axis-var={np.around(np.var(gyr_x), 3)} 
Y-axis-mean={np.around(np.mean(gyr_y), 3)}, Y-axis-var={np.around(np.var(gyr_y), 3)} 
Z-axis-mean={np.around(np.mean(gyr_z), 3)}, Z-axis-var={np.around(np.var(gyr_z), 3)} 
ANSWER:""" 
    return prompt


def generate_prompt_template(args, data_dict, label_dict, target, i:int=0, ground_truth:str="Pos", **kwargs):
    if args.task_type == "imu_HAR":
        pass 
    elif args.task_type == "machine_detection":
        return gen_prompt_tamplate_with_rag_machine(args, data_dict, label_dict, target, i, ground_truth)
    elif args.task_type == "ecg_detection":
        pass
    elif args.task_type == "wifi_localization":
        pass
    elif args.task_type == "wifi_occupancy":    
        pass
