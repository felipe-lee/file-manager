# -*- coding: utf-8 -*-
"""
Picture managers.
"""
import os

from src.utils import DateName, FileRenamer, FileSorter

MEDIA_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.mp4', '.bmp', '.3g2', '.avi', '.3gp', '.mov', '.wmv']


class PictureRenamer(FileRenamer):
    """
    Rename media files based on date
    """
    accepted_extensions = MEDIA_EXTENSIONS
    date_format = "%Y%m%d_%H%M%S"

    def get_new_name(self, file_name):
        """
        Determine new name of file based on earliest date on file.
        :param file_name: Current file name.
        :return: New name for file, or None if no dates associated with file.
        """
        renamer = DateName(file_name=file_name, date_format=self.date_format)

        return renamer.new_name

    def rename_file(self, file_name, new_name, ext):
        new_file_name = "".join([new_name, ext])

        try_renaming = True
        unique_num = 0
        while try_renaming:
            if new_file_name == file_name:
                self.skipped_new_name_matches_old.append(file_name)
                return

            try:
                os.rename(file_name, new_file_name)
                print('new name', new_file_name)
            except WindowsError:
                unique_num += 1
                unique_identifier = f'_{unique_num}'
                new_file_name = "".join([new_name, unique_identifier, ext])
                continue
            except TypeError as e:
                self.failed_to_rename.append(f'Failed to rename {file_name}. Reason: {e}')

                return
            else:
                self.successfully_renamed.append(f'"{file_name}" renamed "{new_file_name}"')

                return


class PictureSorter(FileSorter):
    accepted_extensions = MEDIA_EXTENSIONS

    def move_file(self, file_name):
        sort_key = file_name[0:4]
        current_file_path = '\\'.join([self.input_path, file_name])
        new_file_path = '\\'.join([self.base_path, sort_key, file_name])

        try_moving = True
        unique_num = 0
        while try_moving:
            try:
                os.rename(current_file_path, new_file_path)
                print('new path', new_file_path)
            except WindowsError as error:
                if 'file already exists' in error.strerror:
                    root, ext = os.path.splitext(file_name)
                    unique_num += 1
                    unique_identifier = f'_{unique_num}'
                    new_file_name = "".join([root, unique_identifier, ext])
                    new_file_path = "\\".join([self.base_path, sort_key, new_file_name])
                    continue
                elif 'cannot find the path' in error.strerror:
                    new_dir = '\\'.join([self.base_path, sort_key])
                    os.mkdir(new_dir)
                    continue
                else:
                    try_moving = False
                    print(f'There was an error: {error}')
                    self.failed_to_move.append(file_name)
            else:
                self.successfully_moved.append(f'"{current_file_path}" moved to "{new_file_path}".')

                return
