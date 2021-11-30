import {pathExists, pathExistsSync} from "fs-extra";
import download from "download";
import {existsSync, mkdirSync, WriteFileOptions, writeFileSync} from "fs";

const path = require('path');

export async function downloadAndSaveBatch(fileNames: string[], baseUrl: string, downloadDirectory: string): Promise<any> {
  for(let fileName of fileNames) {
    await downloadAndSave(fileName, baseUrl, downloadDirectory);
  }
}

export function extractUrlAndPath(fileDescriptor: string | FileDescriptor, baseUrl: string, downloadDirectory: string): { fileUrl: string; filePath: string; fileName: string } {

  let fileName, remotePath;

  if(typeof fileDescriptor == "string") {
    fileName = fileDescriptor;
    remotePath = fileDescriptor;
  } else {
    fileName = fileDescriptor.fileName;
    remotePath = fileDescriptor.url;
  }

  const fileUrl: string = `${baseUrl}/${remotePath}`;
  const filePath: string = `${downloadDirectory}/${fileName}`;

  return {fileUrl, filePath, fileName};
}

export async function downloadAndSave(
  fileDescriptor: string | FileDescriptor, baseUrl: string, downloadDirectory: string
): Promise<any> {

  const {fileUrl, filePath, fileName} = extractUrlAndPath(fileDescriptor, baseUrl, downloadDirectory);

  if (pathExistsSyncRecursive(filePath)) {
    return;
  }

  process.stdout.write('Downloading ' + fileName + ': inprogress\x1b[0G');
  return await download(fileUrl).then((data) => {
    writeFileSyncRecursive(filePath, data);
    process.stdout.write('\x1b[2KDownloading ' + fileName + ': done\n');
  });
}

export function pathExistsSyncRecursive(filePath: string): boolean {
  const folders = filePath.split(path.sep).slice(0, -1);
  if (folders.length) {
    let last: string = "";
    for(let folder of folders) {
      last = last == "" ? folder : last + path.sep + folder;
      if (!existsSync(last)) {
        return false;
      }
    }
  }

  return pathExistsSync(filePath);
}

export function writeFileSyncRecursive(filename: string, data: any, options?: WriteFileOptions) {
  const folders = filename.split(path.sep).slice(0, -1);
  if (folders.length) {
    // create folder path if it doesn't exist

    let folderPath: string = "";
    for(let folder of folders) {
      folderPath = folderPath == "" ? folder : folderPath + path.sep + folder;
      if (!existsSync(folderPath)) {
        mkdirSync(folderPath)
      }
    }
  }

  writeFileSync(filename, data, options)
}

export interface FileDescriptor {
  fileName: string;
  url: string
}