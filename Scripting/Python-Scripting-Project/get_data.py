import os
import json
import shutil # for compy and overwrite operations.
from subprocess import PIPE, run # this is going to allow us to run any terminal command that we want.
import sys # this is used to get access to comand line arguments.

GAME_DIR_PATTERN = "game"
GAME_CODE_EXTENSION = ".go"
GAME_COMPILE_COMMAND = ["go", "build"]

def find_all_game_paths(source):
  game_path = []

  for root, dirs, files in os.walk(source):
    for dir_name in dirs:
      if GAME_DIR_PATTERN in dir_name.lower():
        path = os.path.join(source, dir_name)
        game_path.append(path)

    break
  return game_path

def create_dir(path):
  if not os.path.exists(path):
    os.mkdir(path)

def get_name_from_path(paths, strip_path):
  new_name = []
  for path in paths:
    _, dir_name = os.path.split(path)
    new_dir_name = dir_name.replace(strip_path, "")
    new_name.append(new_dir_name)

  return new_name

def copy_and_overite(source, destinantion):
  if os.path.exists(destinantion):
    shutil.rmtree(destinantion)
  shutil.copytree(source, destinantion)

def make_json_metadata_file(path, game_dir):
  data = {
    "gameNames": game_dir,
    "numberOfGames": len(game_dir) 
  }
  with open(path, "w") as f:
    json.dump(data, f)

def compile_code(path):
  code_file_name = None
  for root, dirs, files in os.walk(path):
    for file in files:
      if file.endswith(GAME_CODE_EXTENSION):
        code_file_name = file
        break
    break

  if code_file_name is None:
    return
  
  command = GAME_COMPILE_COMMAND + [code_file_name]

def run_command(command, path):
  cwd = os.getcwd()
  os.chdir(path)

  result = run(command, stdout=PIPE, stdin=PIPE, universal_newlines=True)
  print("Compile Result",result)

def main(source, target):
  # finding paths of source and target directories. 
  cwd = os.getcwd()
  source_path = os.path.join(cwd, source)
  target_path = os.path.join(cwd, target)

  game_paths = find_all_game_paths(source_path)
  new_game_dirs = get_name_from_path(game_paths, "games")
  
  create_dir(target_path)
  
  for src, dest in zip(game_paths, new_game_dirs):
    dest_path = os.path.join(target_path, dest)
    copy_and_overite(src, dest_path)
    compile_code(dest_path)

  json_path = os.path.join(target_path, "metadata.json")
  make_json_metadata_file(json_path, new_game_dirs)

  
if __name__ == "__main__":
  args = sys.argv
  if len(args) != 3:
    raise Exception("Please provide the path to the source and target directory.")
  
  source, target = sys.argv[1:]
  main(source, target)