# Git LFS setup instructions for your project

1. Install Git LFS (if not already installed):
   https://git-lfs.github.com/
   or run:
   git lfs install

2. Track large file types (example: images, models, datasets):
   git lfs track "*.pkl"
   git lfs track "*.h5"
   git lfs track "*.csv"
   git lfs track "static/uploads/*"

3. Add the .gitattributes file to git:
   git add .gitattributes

4. Add and commit your large files as usual:
   git add <large files>
   git commit -m "Track large files with Git LFS"
   git push

# Example tracked types:
# *.pkl
# *.h5
# *.csv
# static/uploads/*

# You can add more patterns as needed.
