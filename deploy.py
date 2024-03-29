#!/usr/env/bin python
# coding:utf-8

import os
import sys
import glob
import locale
import shutil
import argparse
import subprocess

__author__ = 'v1c77'

GIT_REPO = [
    ['origin',  'master', 'git@github.com:v1c77/v1c77.github.io.git'],
    ['coding',  'master', 'git@e.coding.net:Diaoshe/blog.git'],
]

DEPLOY_DIR = 'gh-pages'


def run(cmd):
    print("[+]  "+cmd)
    return subprocess.call(cmd, shell=True)

class ChDir:
    """Context manager for changing the current working directory"""
    def __init__(self, new_path):
        self.newPath = os.path.expanduser(new_path)

    def __enter__(self):
        print(f"[*] work dir changed to {self.newPath}")
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, exception_type, exception_value, traceback):
        print(f"[*] work dir changed back to {self.savedPath}")
        os.chdir(self.savedPath)


def deploy(args):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
    public_dir = os.path.join(current_dir, 'public')
    print("------------------------------------------")
    print(locals())
    print("------------------------------------------")
    commit_msg = 'auto update'
    # no longer submodule commit need.
    # submodule_commit= 'git commit -m "push with master repo"'
    with ChDir(current_dir):
        # step1 clean
        if os.path.exists(public_dir):
            shutil.rmtree(public_dir)

        if args.type == 'first':
            run('rm -rf themes/*')
            run('git submodule init')
            # FIXED https://stackoverflow.com/questions/7605469/git-
            # submodules-pulling-into-a-new-clone-of-the-super-project
            run('git submodule update')
            run("ls  themes/")
            sys.exit(1)

        # on windows set TERM=msys
        s = subprocess.Popen('git log -1 --pretty=format:"%s"',
                             shell=True, stdout=subprocess.PIPE)
        commit_msg = s.communicate()[0].decode('utf-8').encode(locale.getpreferredencoding())
        # step2 build
        # run('hugo -v --cacheDir="./cache"')
        run('hugo -v')

    deploy_dir = os.path.join(parent_dir, DEPLOY_DIR)

    # step3 clone if not exists
    if not os.path.exists(deploy_dir):
        os.makedirs(deploy_dir)
        with ChDir(deploy_dir):
            run('git init')
            for repo in GIT_REPO:
                run(f'git remote add {repo[0]} {repo[2]}')
    elif args.type == 'first':
        with ChDir(deploy_dir):
            run('git init')
            for repo in GIT_REPO:
                run('git remote add {0} {1}'.format(repo[0], repo[2]))

    with ChDir(deploy_dir):
        # step4 clean and pull
        if len(GIT_REPO) > 0:
            print('[+] pull gh-pages...')
            print('git status')
            run('git status')
            print('git add --all')
            run('git status')
            print('git fetch {0}'.format(GIT_REPO[0][0]))
            run('git fetch {0}'.format(GIT_REPO[0][0]))
            # if args.type == 'first':
                # run('git checkout --orphan temp')
                # run('git rm --cached -r .')
                # run('git clean -fdx')
                # run('git branch -D {0}'.format(GIT_REPO[0][1]))
                # run('git checkout -b {0}'.format(GIT_REPO[0][1]))
            # else:
            print('git checkout {0}'.format(GIT_REPO[0][1]))
            run('git checkout {0}'.format(GIT_REPO[0][1]))

            print('git reset --hard {0}/{1}'.format(GIT_REPO[0][0], GIT_REPO[0][1]))
            run('git reset --hard {0}/{1}'.format(GIT_REPO[0][0], GIT_REPO[0][1]))
            run('git clean -fdx')

        # step5 remove all files
        print('[+] remove all files in path {}'.format(deploy_dir))
        for f in os.listdir('.'):
            if f not in ['.git', 'CNAME', 'README.RST']:
                if os.path.isfile(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)

        # step6 copy new files
        print('[+] copy new files from \npath: {} to \n path: {}'
              .format(public_dir, deploy_dir))
        for f in os.listdir(public_dir):
            file_path = os.path.join(public_dir, f)
            if os.path.isfile(file_path):
                shutil.copy(file_path, '.')
            elif os.path.isdir(file_path):
                shutil.copytree(file_path, f)

        # step7 commit and push
        if len(GIT_REPO) > 0:
            run('git add --all')
            run('git commit -a -m "{0}"'.format(commit_msg))
            for repo in GIT_REPO:
                if repo[0] != 'origin':
                    run('git push -f {0} {1}:{2} -u'.format(repo[0], GIT_REPO[0][1], repo[1]))
                else:
                    run('git push {0} {1}:{2} -u'.format(repo[0], GIT_REPO[0][1], repo[1]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='deploy hugo')
    parser.add_argument('type', help='auto or manual')
    parser.add_argument('-t', dest='test', action='store_true', help='for test')
    args = parser.parse_args()
    if args.type in ['auto', 'manual', 'first']:
        deploy(args)
