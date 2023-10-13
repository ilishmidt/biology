import csv
import os
import shutil
import zipfile

from dataclasses import dataclass
from datetime import datetime
from glob import glob
from typing import List, Tuple
from fastapi import UploadFile, HTTPException


PLATE_NAME_LINE_INDEX = 3
PLATE_NAME_VALUE_INDEX = 1
COLUMNS_LINE_INDEX = 7
DATA_START_INDEX_IN_LINES = 8
LINE_IDENTIFIER_INDEX = 4

UPLOAD_DIR = "uploads"


@dataclass
class Data:
    files: dict
    completion_files: dict


@dataclass
class TextFileContent:
    name: str
    columns: list
    data: dict


def process_uploaded_file(file: UploadFile) -> Tuple[str, str, str, str]:
    workdir = os.path.join(UPLOAD_DIR, str(datetime.utcnow()))

    try:
        os.makedirs(name=workdir, exist_ok=True)

        zip_path = os.path.join(workdir, file.filename)
        with open(file=zip_path, mode="wb") as f:
            f.write(file.file.read())

        extracted = os.path.join(workdir, os.path.splitext(file.filename)[0])
        os.makedirs(name=extracted, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(path=extracted)

        result_path = f'{workdir}/result'
        os.makedirs(name=result_path, exist_ok=True)

        return workdir, extracted, zip_path, result_path

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'{e}')


def cleanup(paths: List[str]):
    for path in paths:
        if os.path.exists(path=path):
            shutil.rmtree(path=path)


def move(src: str, dst: str):
    if os.path.exists(path=src):
        shutil.move(src=src, dst=dst)


def make_archive(path_to_zip: str, src: str):
    shutil.make_archive(path_to_zip, 'zip', src)


def read_txt_file(path: str) -> TextFileContent:
    with open(file=path, mode='r') as in_file:
        stripped = (line.strip() for line in in_file)
        lines = [line.split("\t") for line in stripped if line]

        file_name = lines[PLATE_NAME_LINE_INDEX][PLATE_NAME_VALUE_INDEX]
        columns = lines[COLUMNS_LINE_INDEX]

        data = {}
        for line in lines[DATA_START_INDEX_IN_LINES:]:
            line_key = line[:LINE_IDENTIFIER_INDEX]
            data[str(line_key)] = line

        return TextFileContent(name=file_name, columns=columns, data=data)


def get_all_files_paths(directory_path: str, file_type: str) -> List[str]:
    suffix = f'**/*.{file_type}'
    absolute_path = os.path.join(directory_path, suffix)
    return glob(absolute_path, recursive=True)


def read_all_txt_files(path: str) -> Data:
    files = {}
    completion_files = {}

    fps = get_all_files_paths(directory_path=path, file_type='txt')
    for fp in fps:
        text_file_content = read_txt_file(path=fp)
        if 'I' in text_file_content.name:
            completion_files[text_file_content.name] = text_file_content
        else:
            files[text_file_content.name] = text_file_content

    return Data(files=files, completion_files=completion_files)


def write_csv(columns: list, data: list, path: str, file_name: str):
    with open(file=os.path.join(path, f'{file_name}.csv'), mode='w') as f:
        writer = csv.writer(f)
        writer.writerows([columns, *data])


def txt_to_csv_files(workdir: str, data: dict) -> str:
    csv_dir = os.path.join(workdir, 'csv')
    os.makedirs(name=csv_dir)

    for file in data.values():
        write_csv(columns=file.columns, data=list(file.data.values()), path=csv_dir, file_name=file.name)

    return csv_dir
