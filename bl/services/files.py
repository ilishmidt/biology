import csv
import os
import re
import shutil

from datetime import datetime
import zipfile
from dataclasses import dataclass
from glob import glob
from typing import List

import pandas
from fastapi import UploadFile
from fastapi.responses import JSONResponse, FileResponse
from starlette.background import BackgroundTask

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


def merge(file: UploadFile):
    workdir = os.path.join(UPLOAD_DIR, str(datetime.utcnow()))

    try:
        os.makedirs(name=workdir, exist_ok=True)

        zip_path = os.path.join(workdir, file.filename)
        with open(file=zip_path, mode="wb") as f:
            f.write(file.file.read())

        unzip_dir = os.path.join(workdir, os.path.splitext(file.filename)[0])
        os.makedirs(name=unzip_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(unzip_dir)

        data = read_all_txt_files(path=unzip_dir)
        filled_data = fill_missing_rows(data=data)

        csv_dir = os.path.join(workdir, 'csv')
        os.makedirs(name=csv_dir)
        txt_to_csv_files(path=csv_dir, data=filled_data.files)

        result_path = os.path.join(workdir, 'result.csv')
        merge_csvs(output_path=result_path, path=csv_dir)

        return FileResponse(
            path=result_path,
            media_type='application/octet-stream',
            filename='merged.csv',
            background=BackgroundTask(func=_cleanup, path=workdir)
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred: {str(e)}"}
        )


def _cleanup(path: str):
    if os.path.exists(path=path):
        shutil.rmtree(path=path)


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


def fill_missing_rows(data: Data) -> Data:
    for file in data.files.values():
        for completion_file in data.completion_files.values():
            if file.name == re.sub(pattern='\\sI+\\s', repl=' ', string=completion_file.name):
                for row_hash, row_data in completion_file.data.items():
                    if len(row_data) > 4:
                        file.data[row_hash] = row_data
    return data


def write_csv(columns: list, data: list, path: str, file_name: str):
    with open(file=os.path.join(path, f'{file_name}.csv'), mode='w') as f:
        writer = csv.writer(f)
        writer.writerows([columns, *data])


def txt_to_csv_files(path: str, data: dict):
    for file in data.values():
        write_csv(columns=file.columns, data=list(file.data.values()), path=path, file_name=file.name)


def merge_csvs(output_path: str, path: str):
    files = get_all_files_paths(directory_path=path, file_type='csv')
    merged = pandas.concat(map(pandas.read_csv, files), ignore_index=True)
    merged.to_csv(output_path)
