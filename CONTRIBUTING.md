# Contributing to ObjectLens

Thank you for contributing to ObjectLens. To ensure legal compliance and maintain a clean repository history, we require all contributions to follow standard open-source workflows.

## Developer Certificate of Origin (DCO)

We require all commits to be signed off. By signing off your commits, you certify that you have the right to submit the code under the project's open-source license. You can read the full text of the agreement in the [DCO](DCO) file.

### How to Sign Off Your Commits

A valid sign-off must match your Git commit author name and email. It adds a line to your commit message like this:

```text
Signed-off-by: Jane Doe <jane.doe@example.com>
```

#### 1. Signing Off New Commits
Pass the `-s` or `--signoff` flag when committing:
```bash
git commit -s -m "Your commit message"
```

#### 2. Signing Off the Latest Commit
If you forgot to sign off your last commit, amend it:
```bash
git commit --amend --no-edit --signoff
```

#### 3. Signing Off Multiple Previous Commits
If you have multiple commits in your branch that are not signed off, use git rebase to sign them off:

- **Automatic rebase (Git 2.13+)**:
  ```bash
  git rebase --signoff HEAD~N
  ```
  Replace `N` with the number of commits in your PR.

- **Automated command execution**:
  ```bash
  git rebase --exec "git commit --amend --no-edit --signoff" -i HEAD~N
  ```

#### 4. Pushing Your Changes
Since amending and rebasing rewrites commit history, you must force push your branch:
```bash
git push --force-with-lease origin <branch-name>
```

---

## Code Standards and Workflow

- **Backend (Python)**: Format and check code using `ruff`. Run `just lint` and `just format`.
- **Frontend (Vue/TypeScript)**: Follow components standards and run frontend typechecks.
- **Testing**: Add or update test cases for any new features or bug fixes. Run tests with `just test`.
