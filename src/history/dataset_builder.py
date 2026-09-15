import pandas as pd
import json

OUTPUT_DIR = "../../data/history/dataset"

def normalize_track_suffixes(track) -> tuple|str:
    """
    pandas.Series.str.endswith() accepts only a string or a tuple of strings.
    The input data may contain either a single tracking string or a list of them,
    so normalize it before using it in the pandas string operation.
    """
    if isinstance(track, str):
        return track

    if isinstance(track, list):
        return tuple(str(item) for item in track)

    if isinstance(track, tuple):
        return tuple(str(item) for item in track)

    return str(track)

if __name__ == '__main__':
    input_data_path = "../../data/history/samples.json"

    input_data = json.load(open(input_data_path, "r"))
    data = {
        'id_res' : [],
        'package' : [],
        'file' : [],
        'who_introduce' : [],
        'when_introduce' : [],
        'where_introduce' : [],
        'who_remove' : [],
        'when_remove' : [],
        'where_remove' : [],
        'line_tracking' : []
    }

    for pkg in input_data.keys():
        if  input_data[pkg] == {}:
            # skip empty analysis for package
            continue

        for file in input_data[pkg]["files"].keys():
            for commit in input_data[pkg]["files"][file]["commits"].keys():
                # handling introduction
                commit_data = input_data[pkg]["files"][file]["commits"][commit]

                # handling introduction
                if len(commit_data["what_introduce"]) > 0:
                    #print(file + " > " + commit + " > " + f"{commit_data['tracking_strings']}")

                    for elem in commit_data["what_introduce"]:
                        if commit_data["tracking_strings"] is None:
                            elem_occurences = 1
                            data['line_tracking'].append(None)

                        else:
                            elem_occurences = len(commit_data["tracking_strings"][elem])
                            data['line_tracking'].extend(commit_data["tracking_strings"][elem])

                        data['id_res'].extend([elem] * elem_occurences)
                        data['package'].extend([pkg] * elem_occurences)
                        data['file'].extend([file] * elem_occurences)
                        data['who_introduce'].extend([commit_data["who"]] * elem_occurences)
                        data['when_introduce'].extend([commit_data["when"]] * elem_occurences)
                        data['where_introduce'].extend([commit] * elem_occurences)
                        data['who_remove'].extend([None] * elem_occurences)
                        data['when_remove'].extend([None] * elem_occurences)
                        data['where_remove'].extend([None] * elem_occurences)

                aux_df = pd.DataFrame(data)

                # handling removal
                if len(commit_data["what_remove"]) > 0:
                    #mask = data['package'] == pkg and data['file'] == file and data[...]

                    for name, track in commit_data["what_remove"].items():
                        mask = ( (aux_df['package'] == pkg) &
                                 (aux_df['file'] == file) &
                                 (aux_df['id_res'] == name) &
                                 (aux_df['line_tracking'].str.endswith(normalize_track_suffixes(track))))

                        aux_df.loc[mask, "who_remove"] = commit_data["who"]
                        aux_df.loc[mask, "when_remove"] = commit_data["when"]
                        aux_df.loc[mask, "where_remove"] = commit

                data = aux_df.to_dict('list')
                del aux_df

    # save dataset
    pd.DataFrame(data).to_csv(f"{OUTPUT_DIR}/test.csv", index=False)