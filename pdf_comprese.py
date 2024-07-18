# -*- coding: utf-8 -*-
"""
@Time ： 2023/11/3 14:37
@Auth ： RS迷途小书童
@File ：Compress PDF.py
@IDE ：PyCharm
@Purpose：PDF文件压缩
@Web：博客地址:https://blog.csdn.net/m0_56729804
"""
import os
# import fitz
# import PyPDF2
import aspose.pdf as ap
 
# ---------------------------------------无损压缩，但有水印-------------------------------------
 
 
def Lossless_Compression(path1, path2):
    """
    :param path1: 需要压缩的pdf文件路径
    :param path2: 保存的pdf文件路径
    :return: None
    无损压缩，无法去除水印！！！
    """
    compress_path = ap.Document(path1)  # 需要压缩的pdf文件路径
    # print(compress_path)
    optimize = ap.optimization.OptimizationOptions()
    optimize.image_compression_options.compress_images = True
    optimize.image_compression_options.image_quality = 1  # 压缩质量
    compress_path.optimize_resources(optimize)
    compress_path.save(path2)  # 需要压缩后保存的文件路径
    # Evaluation Only. Created with Aspose.PDF. Copyright 2002-2023 Aspose Pty Ltd.无法去除水印
 
import subprocess

def compress_pdf(input_path, output_path, power=3):
    quality = {
        0: '/default',
        1: '/prepress',
        2: '/printer',
        3: '/ebook',
        4: '/screen'
    }
    subprocess.call(['gswin64c', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.5',
                    f'-dPDFSETTINGS={quality[power]}',
                    '-dNOPAUSE', '-dQUIET', '-dBATCH',
                    f'-sOutputFile={output_path}',
                     input_path]
    )
if __name__ == "__main__":
    work_path1 = r'Z:/彭俊喜/.pdf'
    in_path = r"2407,10943.pdf"  # 需要压缩的PDF文件
    out_path = r"2407,10943_c.pdf"  # 压缩后的PDF文件路径
    # Lossless_Compression(in_path, out_path)
    compress_pdf(in_path,out_path)