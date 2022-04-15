import json
import os
import sys
import uuid
from os.path import exists

from pydriller import Repository

from utilities import current_date_and_time


def ask_user_for_dataset_path():
    dataset_path = input("Enter Dataset Path:")
    if not os.path.exists(dataset_path):
        print("Path does not exist")
        sys.exit(1)

    # Traverse the directory and get the names of all the software systems.
    for file in os.listdir(dataset_path):
        f = os.path.join(dataset_path, file)
        if os.path.isdir(f):
            software_system_name = file
            software_system_path = f
            build_key_to_method_id_map(software_system_name, software_system_path)


def build_key_to_method_id_map(software_system_name, software_system_path):
    key_to_method_id_mappings_file = 'output/' + software_system_name + '_key_to_method_id_mappings.json'

    if not exists(key_to_method_id_mappings_file):

        print('Key-to-method ID mappings for ' + software_system_name + ' started at: ' + current_date_and_time.get_current_date_and_time())

        key_to_method_id_dict = {}
        path = ''

        # TODO: Process only the first 100 commits - remove after testing.
        counter = 0

        for commit in Repository(software_system_path, only_modifications_with_file_types=['.java']).traverse_commits():

            # TODO: Process only the first 100 commits - remove after testing.
            counter += 1

            for modified_file in commit.modified_files:

                change_type = modified_file.change_type.name

                match change_type:

                    # If the modification type is an ADDITION, then use the new path as the filepath could not have
                    # existed before the file was created.
                    case 'ADD':
                        path = modified_file.new_path

                    # If the modification type is a DELETION, then use the old path before the file was deleted.
                    case 'DELETE':
                        path = modified_file.old_path

                    # If the modification type is a MODIFICATION, then use the old path because it is still the
                    # same file.
                    case 'MODIFY':
                        path = modified_file.old_path

                    # If the modification type is a RENAMING, then use the new path that the file has been
                    # renamed to.
                    case 'RENAME':
                        path = modified_file.new_path

                assert path != ''

                # Process only Java source code files.
                if path.endswith('.java'):

                    # Exclude test files.
                    if not path.endswith('Test.java'):

                        modified_methods = modified_file.changed_methods

                        for modified_method in modified_methods:
                            class_name_and_method_signature = modified_method.long_name
                            key = path + '=+=' + class_name_and_method_signature
                            method_id = str(uuid.uuid4())
                            key_to_method_id_dict[key] = method_id

            # TODO: Process only the first 100 commits - remove after testing.
            if counter == 100:
                break

        with open(key_to_method_id_mappings_file, 'w') as json_file:
            json.dump(key_to_method_id_dict, json_file)

        print('Key-to-method ID mappings for ' + software_system_name + ' completed at: ' + current_date_and_time.get_current_date_and_time())

    else:
        print('key_to_method_id_mappings_file for ' + software_system_name + ' already exists.')

    parameter_list = [
        software_system_name,
        software_system_path,
        key_to_method_id_mappings_file
    ]

    load_key_to_method_id_mappings(parameter_list)


def load_key_to_method_id_mappings(parameter_list):
    key_to_method_id_mappings_file = parameter_list[2]

    # Open JSON file.
    json_file = open(key_to_method_id_mappings_file)

    # Load JSON file.
    key_to_method_id_mappings_json_data = json.load(json_file)

    # Close JSON file.
    json_file.close()

    parameter_list.append(key_to_method_id_mappings_json_data)

    build_method_level_transaction_database(parameter_list)


def build_method_level_transaction_database(parameter_list):
    software_system_name = parameter_list[0]
    software_system_path = parameter_list[1]
    key_to_method_id_mappings_json_data = parameter_list[3]

    transaction_database_json_file = 'output/' + software_system_name + '_method_level_transaction_database.json'

    if not exists(transaction_database_json_file):

        print('Transaction database construction for ' + software_system_name + ' started at: ' + current_date_and_time.get_current_date_and_time())

        commits = []
        path = ''

        # TODO: Process only the first 100 commits - remove after testing.
        counter = 0

        for commit in Repository(software_system_path, only_modifications_with_file_types=['.java']).traverse_commits():

            # TODO: Process only the first 100 commits - remove after testing.
            counter += 1

            commit_hash = commit.hash
            paths = set()

            for modified_file in commit.modified_files:

                change_type = modified_file.change_type.name

                match change_type:

                    # If the modification type is an ADDITION, then use the new path as the filepath could not have
                    # existed before the file was created.
                    case 'ADD':
                        path = modified_file.new_path

                    # If the modification type is a DELETION, then use the old path before the file was deleted.
                    case 'DELETE':
                        path = modified_file.old_path

                    # If the modification type is a MODIFICATION, then use the old path because it is still the
                    # same file.
                    case 'MODIFY':
                        path = modified_file.old_path

                    # If the modification type is a RENAMING, then use the new path that the file has been
                    # renamed to.
                    case 'RENAME':
                        path = modified_file.new_path

                assert path != ''

                modified_methods = []

                # Process only Java source code files.
                if path.endswith('.java'):

                    # Exclude test files.
                    if not path.endswith('Test.java'):

                        changed_methods = modified_file.changed_methods

                        for changed_method in changed_methods:
                            class_name_and_method_signature = changed_method.long_name

                            # Reconstruct the key as initially constructed in the 'build_key_to_method_id_map' method
                            # above, and use the key to  method IDs.
                            key = path + '=+=' + class_name_and_method_signature
                            paths.add(path)

                            try:
                                method_id = key_to_method_id_mappings_json_data[key]
                                modified_methods.append(method_id)
                            except KeyError:
                                print('Key not found in key-to-method ID mappings file: ' + key)

                        commit_details_dict = {
                            'commit_hash': commit_hash,
                            'commit_details': [{
                                'path': path,
                                'number_of_affected_java_source_code_files': len(paths),
                                'modified_methods': modified_methods
                            }]
                        }

            # Only add commits if they have not been added before.
            if commit_details_dict not in commits:
                # Only add commits that have at least one modified method.
                if len(commit_details_dict['commit_details'][0]['modified_methods']) > 0:
                    commits.append(commit_details_dict)

            # TODO: Process only the first 100 commits - remove after testing.
            if counter == 100:
                break

            with open(transaction_database_json_file, 'w') as json_file:
                json.dump(commits, json_file)

            parameter_list.append(transaction_database_json_file)

        print('Transaction database construction for ' + software_system_name + ' completed at: ' + current_date_and_time.get_current_date_and_time())

        update_transaction_database(parameter_list)
    else:
        print('A transaction database already exists for ' + software_system_name + '.')


def update_transaction_database(parameter_list):
    software_system_name = parameter_list[0]

    print('Transaction database Update for ' + software_system_name + ' started at: ' + current_date_and_time.get_current_date_and_time())

    transaction_database_json_file = parameter_list[4]

    # Open JSON file.
    json_file = open(transaction_database_json_file)

    # Load JSON file.
    transaction_database = json.load(json_file)

    for i in transaction_database:
        transaction_frequency = 1
        commit_hash_outer = i['commit_hash']
        commit_details_outer = i['commit_details']
        for j in commit_details_outer:
            modified_methods_outer = j['modified_methods']
            for k in transaction_database:
                commit_hash_inner = k['commit_hash']
                commit_details_inner = k['commit_details']
                for m in commit_details_inner:
                    modified_methods_inner = m['modified_methods']
                    if commit_hash_outer != commit_hash_inner:
                        if set(modified_methods_outer) == set(modified_methods_inner):
                            transaction_frequency += 1

            # Update the transaction frequency in the transaction database.
            j['transaction_frequency'] = transaction_frequency

    with open(transaction_database_json_file, 'w') as json_file:
        json.dump(transaction_database, json_file)

    # Close JSON file.
    json_file.close()

    print('Transaction database Update for ' + software_system_name + ' completed at: ' + current_date_and_time.get_current_date_and_time())


if __name__ == '__main__':
    ask_user_for_dataset_path()
