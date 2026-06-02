import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from views.main_view import MainView

def main():
    MainView().run()

if __name__ == '__main__':
    main()