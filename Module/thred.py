import os

def read_thred(name):
    # 获取当前目录
    current_directory = os.getcwd()
    # 拼接文件路径
    file_path = os.path.join(current_directory, name)

    # 读取文件内容
    with open(file_path, 'r') as file:
        content = file.read()

    # 将字符串拆分成数字列表
    numbers = list(map(int, content.split(',')))
    return numbers

def save_thred(list,name):
    # 获取当前目录
    current_directory = os.getcwd()
    # 将数字列表转换回字符串
    updated_content = ','.join(map(str, list))

    # 写入到新的 txt 文件
    output_file_path = os.path.join(current_directory, 'thred.txt')
    with open(output_file_path, 'w') as file:
        file.write(updated_content)
