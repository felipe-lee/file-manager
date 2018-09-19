# -*- coding: utf-8 -*-
"""
Base utilities to manage files.
"""
import os
from datetime import datetime

import exifread


def format_date_time(date_time, date_format):
    """
    Takes input timestamp and returns a string in the format input.
    :param date_time: timestamp
    :param date_format: datetime format to return string as.
    :return:
    """
    dtime = datetime.fromtimestamp(date_time)

    return dtime.strftime(date_format)


def get_file_extension(file_name):
    root, extension = os.path.splitext(file_name)

    return extension


class DateName(object):
    """
    This object takes in a file and a date format and determines what the name of the file would be if it was the
    oldest datetime associated with the object (creation or modification time, or even taken time if an image).
    """

    def __init__(self, file_name, date_format):
        """
        Finds new name on init.
        :param file_name: Name of file.
        :param date_format: datetime format for new name string.
        """
        self.file_name = file_name
        self.date_format = date_format
        self.new_name = None

        self.determine_name()

    def determine_name(self):
        """
        Gathers all the possible dates for the input file and sets the name to the oldest datetime.
        :return: Oldest possible date for the file.
        """
        date_times = [self.get_date_created(), self.get_date_taken(), self.get_date_modified()]

        try:
            self.new_name = min(date for date in date_times if date is not None)
        except ValueError:
            # Occurs if every date is None. Just won't set a value for self.new_name
            pass

    def get_date_created(self):
        """
        Gets creation date of the file based on the information the system has.
        :return: Returns the date the file was created in the format specified, or if no date found returns None.
        """
        date_created = os.path.getctime(filename=self.file_name)

        if date_created:
            return format_date_time(date_time=date_created, date_format=self.date_format)

    def get_date_modified(self):
        """
        Gets modification date of the file based on the information the system has.
        :return:  Returns the date the file was last modified in the format specified, or if no date found returns None.
        """
        date_modified = os.path.getmtime(filename=self.file_name)

        if date_modified:
            return format_date_time(date_time=date_modified, date_format=self.date_format)

    def get_date_taken(self):
        """
        Gets the date the image was taken. If not an image or no tag containing the pertinent information is found,
        then this returns None. Otherwise it returns the date in the format specified.
        :return:
        """
        with open(self.file_name, 'rb') as fh:
            # Read all tags up to and including the stop tag. Returns dictionary of tags read.
            tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")

            try:
                date_taken = tags.get("EXIF DateTimeOriginal").values
            except AttributeError:
                return
            else:
                return date_taken.replace(':', '').strip().replace(' ', '_')


class FileRenamer(object):
    """
    Utility to rename a set of flies based on whatever rules subclass this object. This object will not work on its own,
    you need to subclass it to set up rules for determining the new name and for actually renaming the file.
    """

    accepted_extensions = []  # Extensions of files that should be renamed.

    def __init__(self, input_path=None):
        """
        Attempts to retrieve files. If files are found, processes them to rename them.
        :param input_path: Optional path to search for files. If no path is input, this will run in the current
            directory.
        """
        self.input_path = input_path
        self.original_path = os.getcwd()
        self.path = self.input_path or self.original_path

        self.files = []
        self.successfully_renamed = []
        self.skipped_new_name_matches_old = []
        self.failed_to_rename = []
        self.skipped_different_extension = []

        self.get_files()

        if self.files:
            self.process_files()

        self.print_report()

    def get_files(self):
        """
        Search directory for files. If the path does not exist, inform user and ask if they want to continue. If they
        do, then they need to input a new path. Will continue to try to find files until the path resolves and the
        directory contents are dumped into self.files, or until the user indicates they no longer want to continue.
        :return: Nothing. Sets self.files attribute.
        """
        directory_found = False
        while not directory_found:
            try:
                self.files = os.listdir(self.path)
            except WindowsError:
                continue_running = input('The path "{input_path}" was not found. Do you want to continue? (Y/N)'.
                                         format(input_path=self.path)).upper()

                if continue_running == 'N':
                    return
                elif continue_running == 'Y':
                    self.path = input("Please enter a new path:")

                    continue
                else:
                    print("You did not input a correct value to answer if you wanted to continue.")

                    return
            else:
                directory_found = True

    def get_new_name(self, file_name):
        """
        Hook to allow determination of new file name.
        :param file_name: current file name
        :return: whatever gets returned by sub-class.
        """
        raise NotImplementedError('You need to subclass this and override this method')

    def rename_file(self, file_name, new_name, ext):
        """
        Hook to rename file.
        :param file_name: current file name
        :param new_name: new name of file
        :param ext: extension of file
        :return: whatever gets returned by sub-class
        """
        raise NotImplementedError('You need to subclass this and override this method')

    def process_files(self):
        """
        Run through files and attempt to rename them.
        :return: None, updates instance attributes.
        """
        for file_name in self.files:
            print('file_name', file_name)
            ext = get_file_extension(file_name)

            # Make all file names be the full path to file.
            file_name = os.path.join(self.path, file_name)

            if ext.lower() not in self.accepted_extensions:
                self.skipped_different_extension.append(file_name)
                continue

            new_name = self.get_new_name(file_name=file_name)

            if new_name is None:
                self.failed_to_rename.append(f'Failed to rename {file_name} because no new name could be determined.')

                continue

            # Make all new file names be the full path to file.
            new_name = os.path.join(self.path, new_name)

            self.rename_file(file_name=file_name, new_name=new_name, ext=ext)

    def print_report(self):
        print(f'Successfully updated {len(self.successfully_renamed)} files.')

        print(f'Failed to rename {len(self.failed_to_rename)} files.')

        print(f'Skipped {len(self.skipped_new_name_matches_old)} because new name matched old name.')

        print(f'Skipped {len(self.skipped_different_extension)} because extension did not match approved list.')


class FileSorter(object):
    accepted_extensions = []

    def __init__(self, input_path, base_path):
        self.input_path = input_path
        self.base_path = base_path

        self.files = []
        self.successfully_moved = []
        self.failed_to_move = []
        self.skipped_different_extension = []

        self.get_files()

        if self.files:
            self.process_files()

        self.print_report()

    def get_files(self):
        directory_found = False
        while not directory_found:
            try:
                self.files = os.listdir(self.input_path)
            except WindowsError:
                continue_running = input(f'The path "{self.input_path}" was not found. Do you want to continue? (Y/N)')
                if continue_running.upper() == 'N':
                    return
                elif continue_running.upper() == 'Y':
                    self.input_path = input("Please enter a new path:")
                    continue
                else:
                    print("You did not input a correct value to answer if you wanted to continue.")
                    return
            else:
                directory_found = True

    def move_file(self, file_name):
        pass

    def process_files(self):
        for file_name in self.files:
            print('file_name', file_name)
            ext = get_file_extension(file_name)

            if ext.lower() not in self.accepted_extensions:
                self.skipped_different_extension.append(file_name)
                continue

            self.move_file(file_name)

    def print_report(self):
        print(f'Successfully moved {len(self.successfully_moved)} files.')

        print(f'Failed to move {len(self.failed_to_move)} files.')

        print(f'Skipped {len(self.skipped_different_extension)} because extension did not match approved list.')
