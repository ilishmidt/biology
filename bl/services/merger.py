import os
import re
import pandas

from fastapi import UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

import bl.services.files as files_service


def merge(file: UploadFile) -> FileResponse:
    workdir, extracted = files_service.process_uploaded_file(file=file)

    data = files_service.read_all_txt_files(path=extracted)
    completed_data = apply_completion_files(data=data)

    csv_dir = files_service.txt_to_csv_files(workdir=workdir, data=completed_data.files)

    result_path = merge_csvs(workdir=workdir, path=csv_dir)

    return FileResponse(
        path=result_path,
        media_type='application/octet-stream',
        filename='merged.csv',
        background=BackgroundTask(func=files_service.cleanup, path=workdir)
    )


def apply_completion_files(data: files_service.Data) -> files_service.Data:
    for file in data.files.values():
        for completion_file in data.completion_files.values():
            if file.name == re.sub(pattern='\\sI+\\s', repl=' ', string=completion_file.name):
                for row_hash, row_data in completion_file.data.items():
                    if len(row_data) > 4:
                        file.data[row_hash] = row_data
    return data


def merge_csvs(workdir: str, path: str) -> str:
    result_path = os.path.join(workdir, 'result.csv')

    files = files_service.get_all_files_paths(directory_path=path, file_type='csv')
    merged = pandas.concat(map(pandas.read_csv, files), ignore_index=True)
    merged.to_csv(result_path)
    return result_path
