import os
import pandas as pd

import re


def foo():
    name = '09-ZL-08堵水作业.xlsx'
    m = re.match(r'^([0-9a-zA-Z\-]+)(.*)$', name)
    print(m.groups())


re_numbered_name = re.compile(r'^([0-9a-zA-Z\_]+)(.*)$')
re_code_type = re.compile(r'^([0-9a-zA-Z\-]+)(.*)$')


def new_name_from_old(old):
    m = re_numbered_name.match(old)
    return '_'.join(m.groups())


# new_name_from_old(name)


def is_pdf(file):
    return file.split('.')[1] == 'pdf'


def is_excel(file):
    suffix = file.split('.')[1]
    return suffix == 'xls' or suffix == 'xlsx'


def convert_dir(path):
    files = os.listdir(path)
    pdfs = [file for file in files if is_pdf(file)]
    xls = [file for file in files if is_excel(file)][0]
    print('converting', path)
    # print(pdfs)
    convert_pdf(path, pdfs)
    convert_excel(path, xls)


def convert_pdf(path, pdf):
    for old_name in pdf:
        new_name = new_name_from_old(old_name)
        print(old_name)
        os.rename(os.path.join(path, old_name), os.path.join(path, new_name))


def convert_excel(path, excel):
    df = pd.read_excel(os.path.join(path, excel))
    old_names = df['编号名称']
    new_names = []
    for old_name in old_names:
        new_names.append(new_name_from_old(old_name))
    df['编号名称'] = new_names
    rcode, rtype = re_code_type.match(excel).groups()
    df['资源分类'] = [rtype.split('.')[0]] * len(df)
    df['编号'] = [rcode] * len(df)
    df['资源类型'] = ['专利'] * len(df)
    df = df.reindex_axis(['编号', '资源类型', '资源分类', '名称', '编号名称', '数据格式', '关键词', '摘要', '申请号',
                          '申请日', '公开（公告）号', '公开（公告）日', 'IPC分类号', '申请（专利权）人', '发明人',
                          '优先权号', '优先权日', '申请人地址', '申请人邮编', 'CPC分类号'], axis=1)
    df.to_excel(os.path.join(path, excel), index=False)


def main():
    base_dir = ['井下作业', '录井']
    for base in base_dir:
        sub_fir = os.listdir(base)
        for sub in sub_fir:
            convert_dir(os.path.join(base, sub))


if __name__ == '__main__':
    main()
    # foo()
