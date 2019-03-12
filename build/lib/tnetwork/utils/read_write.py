import csv

def write_list_of_list(list_of_list,file,sep='\t'):
    with open(file, mode='w') as to_write:
        to_write = csv.writer(to_write, delimiter=sep, quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for list in list_of_list:
            to_write.writerow(list)