import hashlib
import os
import sys
import zipfile
from types import ModuleType
from typing import Any, Optional, Set
from zipfile import ZipFile


src_name = os.path.realpath(f"{__file__}/../src")
if src_name not in sys.path:
    sys.path.insert(0, src_name)

import app
from bean import beans

verbose = False


def init_hack():
    # Because some beans are lazily loaded, create the instances in order to ensure they are included in the archive
    beans.load_all_lazy()


def check_args():
    target = None
    for v in sys.argv[1::]:
        if v == "-v":
            global verbose
            verbose = True
        elif target is None:
            target = v
        else:
            print(f"Invalid command line argument: {v}", file=sys.stderr)
            exit(2)
    if target is None:
        print("Please supply target zip file name.", file=sys.stderr)
        exit(2)
    return target


def ensure_parent_exists(file_name: str):
    """
    For the given absolute file name, ensure the parent folder for the file exists.
    :param file_name: the fully-qualified file name.
    """
    parent = os.path.split(file_name)[0]
    if parent is not None and len(parent) > 0 and not os.path.isdir(parent):
        os.makedirs(parent)


def __find_root_dir(path: str):
    check_path = path
    while True:
        file_name = os.path.join(check_path, ".git")
        if os.path.isdir(file_name):
            return check_path + os.sep
        check_path, child = os.path.split(check_path)
        if len(child) == 0:
            break
    raise EnvironmentError(f"Unable to find .git in {path}.")


def add_json_resources(zip: ZipFile):
    for root, dirs, files in os.walk(src_name):
        for file in files:
            if not file.endswith(".json"):
                continue
            full_path = os.path.join(root, file)
            name = os.path.relpath(full_path, src_name)
            if verbose:
                print(f"{full_path} => {name} ...")
            zip.write(full_path, name)


def zip_python_files(source_module: ModuleType,
                     target_file: str):
    modules_done = set()
    root_dir = __find_root_dir(os.path.split(source_module.__file__)[0])

    def module_map(m: Any) -> Optional[ModuleType]:
        t = type(m)
        if t is not ModuleType:
            if hasattr(m, "__module__"):
                m = m.__module__
            else:
                return None
            m = sys.modules[m]

        file_name = m.__dict__.get('__file__')
        if file_name is None or not file_name.startswith(root_dir):
            return None
        if type(m) is ModuleType and hasattr(m, "__file__") and "python3" not in getattr(m, "__file__"):
            return m
        else:
            return None

    def collect_them(module_set: Set, module: ModuleType):
        if module in module_set:
            return
        module_set.add(module)
        values = list(filter(lambda v: v is not None, map(module_map, module.__dict__.values())))
        for value in values:
            collect_them(module_set, value)

    collect_them(modules_done, source_module)

    # For some reason we seem to miss the __init__.py files, so take another pass
    parent = os.path.split(source_module.__file__)[0] + "/"

    for v in sys.modules.values():
        if v not in modules_done and hasattr(v, "__file__"):
            f = v.__file__
            if f is not None and f.startswith(parent):
                modules_done.add(v)

    # for k, v in sys.modules.items():
    #     if hasattr(v, "__file__"):
    #         print(k, getattr(v, "__file__"))

    ensure_parent_exists(target_file)
    temp_name = target_file + ".temp"
    good = False
    try:
        with zipfile.ZipFile(temp_name, "w") as zip:
            for mod in modules_done:
                if mod.__dict__.get('_EXCLUDE_FROM_BUILD') is not None:
                    print(f"Skipping {mod.__file__}")
                    continue
                file_name = mod.__file__
                archive_name = os.path.relpath(file_name, src_name)
                if verbose:
                    print(f"{file_name} -> {archive_name} ...")
                zip.write(file_name, archive_name)
            add_json_resources(zip)

        good = True
        print(f"Saved {len(modules_done)} files to {target_file}.")
    finally:
        if not good:
            if os.path.isfile(temp_name):
                os.remove(temp_name)

    if os.path.isfile(target_file):
        os.remove(target_file)
    os.rename(temp_name, target_file)
    return target_file


def show_checksum(file_name: str):
    with open(file_name, "rb") as f:
        data = f.read()
        m = hashlib.sha256(data)
        print(f"Hash: {m.digest().hex()}")


init_hack()
zip_file = zip_python_files(app, check_args())
show_checksum(zip_file)
