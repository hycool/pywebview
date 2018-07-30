import qt5_cef
import os

if __name__ == '__main__':
    # qt5_cef.launch_main_window(url='file:///{dirName}/index.html'.format(dirName=os.path.dirname(__file__)),
    #                            context_menu=True)

    qt5_cef.create_window(url='file:///{dirName}/index.html'.format(dirName=os.path.dirname(__file__)),
                          context_menu=True)
