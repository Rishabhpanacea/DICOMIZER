import os


def CheckAlldicomFiles(Path):
    files = os.listdir(Path)
    for file in files:
        filePath = os.path.join(Path, file)
        if os.path.isfile(filePath):
            print(f"'{filePath}' is a file.")
            if os.path.isfile(filePath) and filePath.lower().endswith('.dcm'):
                print(f"'{filePath}' is a .dcm file.")
            else:
                return False
        elif os.path.isdir(filePath):
            print(f"'{filePath}' is a directory.")
            return False
        else:
            print(f"'{filePath}' is neither a file nor a directory or doesn't exist.")
            return False
    return True


def FindAllDCMSeries(Path):
    if os.path.isfile(Path):
        print(f"'{Path}' is a file.")
        return []

    elif os.path.isdir(Path):
        print(f"'{Path}' is a directory.")
        if CheckAlldicomFiles(Path):
            return [Path]
        
        files = os.listdir(Path)
        output = []
        for file in files:
            output = output + FindAllDCMSeries(os.path.join(Path,file))
        return output
    else:
        print(f"'{Path}' is neither a file nor a directory or doesn't exist.")
        return []
