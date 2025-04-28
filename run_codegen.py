import os
import time
import argparse
from ament_index_python.packages import get_package_share_directory
from casadi import *
from src import *



# TODO: REPEAT BENCHMARK WITH TORCH VMAP INSTEAD OF VECTORIZING WITH DICT.
def main(args):
    casadi_fns = []
    # fn_dir = CUSADI_BENCHMARK_DIR if args.codegen_benchmark_fns else CUSADI_FUNCTION_DIR
    try:
    # 获取ROS2包的共享目录路径
        package_path = get_package_share_directory("optimal_control_problem")

        # 拼接子目录路径
        fn_dir = os.path.join(package_path, "code_gen")

        # 验证路径是否存在
        if not os.path.exists(fn_dir):
            print(f"警告：路径 {fn_dir} 不存在，可能需要手动创建或检查包安装")
        else:
            print(f"代码生成目录：{fn_dir}")

    except PackageNotFoundError:
        print(f"错误：包 'optimal_control_problem' 未找到，请确保：")
        print("1. 已通过 colcon build 编译该包")
        print("2. 当前环境已 source install/setup.bash")
    for filename in os.listdir(fn_dir):
        f = os.path.join(fn_dir, filename)
        if os.path.isfile(f) and f.endswith(".casadi"):
            if args.fn_name == "all" or args.fn_name in f:
                print("CasADi function found: ", f)
                casadi_fns.append(casadi.Function.load(f))
    for f in casadi_fns:
        if args.precision:
            print("Generating double code")
            generateCUDACodeDouble(f)
        else:
            print("Generating float code")
            generateCUDACodeFloat(f)
        # generateCUDACodeFloat(f)
        # generateCUDACodeDouble(f)
        if args.gen_pytorch:
            generatePytorchCode(f)
    generateCMakeLists(casadi_fns)
    t_compile = time.time()
    compileCUDACode()
    t_compile = time.time() - t_compile
    print(f"Compilation time: {t_compile:.2f} seconds")

# Helper functions
def compileCUDACode():
    print("Compiling CUDA code...")
    status = os.system("cd build && cmake .. && make -j")
    if status == 0:
        print("Compilation complete.")
    else:
        print("Compilation failed.")
        exit(1)
        
def printParserArguments(parser, args):
    # Print out all arguments, descriptions, and default values in a formatted manner
    print(f"\n{'Argument':<20} {'Description':<80} {'Default':<10} {'Current Value':<10}")
    print("=" * 140)
    for action in parser._actions:
        if action.dest == 'help':
            continue
        arg_strings = ', '.join(action.option_strings)
        description = action.help or 'No description'
        default = action.default if action.default is not argparse.SUPPRESS else 'No default'
        current_value = getattr(args, action.dest, default)
        print(f"{arg_strings:<20} {description:<80} {default:<10} {current_value:<10}")
    print()

def setupParser():
    parser = argparse.ArgumentParser(description='Script to generate parallelized code from CasADi functions')
    parser.add_argument('--fn', type=str, dest='fn_name', default='all',
                        help='Function to parallelize in cusadi/casadi_functions, defaults to "all"')
    parser.add_argument('--precision', type=bool, dest='precision', default=True,
                        help='Precision of generated fn. True: double, False: float. Defaults to double')
    parser.add_argument('--gen_CUDA', type=bool, dest='gen_CUDA', default=True,
                        help='Generate CUDA codegen. Defaults to True')
    parser.add_argument('--gen_pytorch', type=bool, dest='gen_pytorch', default=False,
                        help='Generate Pytorch codegen in addition to CUDA. Defaults to False')
    parser.add_argument('--benchmark', type=bool, dest='codegen_benchmark_fns', default=False,
                        help='Generate functions for benchmarking. Defaults to False')
    return parser

if __name__ == "__main__":
    parser = setupParser()
    args = parser.parse_args()
    printParserArguments(parser, args)
    main(args)