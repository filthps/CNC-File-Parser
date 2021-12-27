from decorators import file_locker, re_numerate


@file_locker
@re_numerate
def main(full_path, **kwargs):
    #with open(full_path) as file:
        #pass
    print(**kwargs)
