import argparse

from imports import *
parser = argparse.ArgumentParser()

parser.add_argument(
    "--task_type",
    choices=["imu_HAR", "machine_detection", "ecg_detection", "wifi_localization", "wifi_occupancy"],
    default="imu_HAR",
    help="Type of IoT task to run",
)
parser.add_argument(
    "--cls_num",
    type=int,
    default=2,
    help="Number of classes to classify (just used in imu_HAR task)",
)
parser.add_argument(
    "--sample_num",
    type=int,
    default=50,
    help="Number of samples to generate",
)
parser.add_argument(
    "--no_domain_knowledge",
    action="store_true",
    help="Whether to use domain knowledge",
)
parser.add_argument(
    "--no_demo_knowledge",
    action="store_true",
    help="Whether to use demo knowledge",
)
parser.add_argument(
    "--model",
    choices=["gpt3.5", "gpt4", "llama2", "Mistral-7b", "Gemini", "Haiku"],
    # llama2，Mistral-7b，Gemini，Claude3 Haiku
    default="gpt4",
    help="Model to use for generation",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="Whether to run in debug mode. Note in debug mode, just print retrieved knowledge and final prompt, don't generate result.",
)
parser.add_argument(
    "--device",
    choices=["cpu", "cuda"],
    default="cuda",
    help="Device to run the model on",
)

parser.add_argument(
    "--data_path",
    type=str,
    default="data",
    help="Path to the data directory",
)
parser.add_argument(
    "--knowledge_path",
    type=str,
    default="knowledge",
    help="Path to the knowledge directory",
)
parser.add_argument(
    "--output_file_path",
    type=str,
    default="results/output.log",
    help="Path to the output file",
)

args = parser.parse_args()
args.role_des = Role_des[args.task_type]
