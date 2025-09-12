git checkout -b <branch-name> #make branch
ls #list of stuff in file
cd #go to file
touch <file-name> #make file
rm <file-name> #delete file
git status #checks status
git pull --rebase #updates code to most modern version
git checkout <branch-name> #moves to other branch
git rebase #updates local code to main code
git stash #stores the file without commit
pip3 install -r requirements.txt #installs all libraries in file
git branch #lists branches
git rebase origin/main #updates branch to main file
python3 -m <file name> #runs code
git rm <file name> #tell git you removed file
pip3 install <module> #installs indivisual library
source ~/.zshrc #updates terminal
cd .. #take you out of folder you are in
git log #show all changes
rm -rf <file name> #deletes file
git reset --hard HEAD~1 #uncommits stuff
git rm <file name> #adds delete file to commit

#steps for adding file
1. git add #stages file for commit
2. git commit -m"message" #commits file for adding to github
3. git push # use to check upstream branch
4. git push example # add upstream branch from error code

#steps for updating local code
1. git checkout main #goes to main branch
2. git pull --rebase #updates