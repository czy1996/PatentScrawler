from scrawler import download_filename
from multiprocessing import Process, Pool
from utils import log
import os


# class DownLoadFile(Process):
#     def __init__(self, filename):
#         super().__init__()
#         self.filename = filename
#
#     def run(self):
#         log('启动进程{} {}'.format(self.pid, self.filename))
#         download_filename(self.filename)

def test_worker(path, filename):
    log(path, filename)


def main():
    path = 'origin'
    filenames = os.listdir('origin')
    pool = Pool(processes=2)
    for i, filename in enumerate(filenames):
        log('启动进程{} {}'.format(i, filename))
        x = pool.apply_async(download_filename, args=(path, filename))
        # x.get()
    pool.close()
    pool.join()

if __name__ == '__main__':
    main()