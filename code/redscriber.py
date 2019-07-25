import os
import praw.exceptions
import datetime


class RedditCommentTranscriber:

    def __init__(self):
        self._reddit = praw.Reddit('auth_info')  # auth information stored in git-ignored praw.ini file for
        # confidentiality

    def transcribe(self, start_comment_id, end_comment_id):
        start_comment = self._reddit.comment(id=start_comment_id)

        try:
            start_comment.refresh()  # obtains the CommentForest (i.e. list) of replies
            start_comment.replies.replace_more(limit=None)  # loads deeply-nested comments
        except praw.exceptions.ClientException:
            print('Start comment does not exist.')
            return

        file_name = str(datetime.datetime.utcnow().date()) + '_' + start_comment_id + '_' + end_comment_id + '.txt'
        save_file = open(file_name, 'w')


        if end_comment_id == 'none' or start_comment_id == end_comment_id:
            self._print_single_comment(start_comment)
        elif end_comment_id == 'all':
            self._print_comment_tree(start_comment, 0)
        else:
            self._print_comment_chain(start_comment, end_comment_id, 0, list())

    @staticmethod
    def _indent_level(level):
        indent_string = ''

        for i in range(level):
            indent_string = indent_string + '| '

        return indent_string

    @staticmethod
    def _print_single_comment(comment):  # todo: insert new line breaks when line overflows
        print('https://www.reddit.com' + comment.permalink)
        print('Transcribed', datetime.datetime.utcnow())
        print()
        print(comment.author.name + ' ', str(comment.score), 'points ',
              datetime.datetime.fromtimestamp(comment.created_utc), ' #' + comment.id)
        print(comment.body)
        print()

    def _print_comment_tree(self, root_comment, level):  # todo: insert new line breaks when line overflows
        if level == 0:
            print('https://www.reddit.com' + root_comment.permalink)
            print('Transcribed', datetime.datetime.utcnow())
            print()

        indent_string = self._indent_level(level)

        try:
            print(indent_string + root_comment.author.name + ' ', str(root_comment.score), 'points ',
                  datetime.datetime.fromtimestamp(root_comment.created_utc), ' #' + root_comment.id)
            comment_body_lines = root_comment.body.splitlines()
            for line in comment_body_lines:
                print(indent_string + line)
        except AttributeError:
            print(indent_string + 'deleted/removed', ' #' + root_comment.id)
        print(indent_string)

        for reply in root_comment.replies:
            self._print_comment_tree(reply, level + 1)

    # Recursive depth-first search from the start comment to find the end comment
    # If end comment is found, adds the chain to the comment_stack and finally prints the comment_stack.
    # Returns True if end_comment is found in root_comment's descendants, False if it has not been found.
    def _print_comment_chain(self, root_comment, end_comment_id, level, comment_stack):  # todo: insert new line breaks when line overflows
        # Base case: root_comment is the end comment
        if root_comment.id == end_comment_id:
            comment_stack.append(root_comment)
            return True

        # Search through children to see if any of them are an ancestor of the end comment. If so, root_comment
        # is also an ancestor and therefore part of the chain, so add it to the comment stack
        found = False
        for reply in root_comment.replies:
            if self._print_comment_chain(reply, end_comment_id, level+1, comment_stack):
                comment_stack.append(root_comment)
                found = True
                if level != 0:
                    return found
                else:
                    break

        # If end comment is not found in root_comment's descendants, return False
        if not found:
            if level == 0:
                print('End comment was not found in thread.')
            return False

        # We will only reach this code if we are at the starting comment, the end-comment has been found, and
        # comment_stack contains the entire chain of comments with the starting comment on top and the ending
        # comment on bottom.
        # This code prints every comment on the comment_stack.
        while comment_stack:
            current = comment_stack.pop()
            if level == 0:
                print('https://www.reddit.com' + root_comment.permalink)
                print('Transcribed', datetime.datetime.utcnow())
                print()
            indent_string = self._indent_level(level)
            level += 1

            try:
                print(indent_string + current.author.name + ' ', str(current.score), 'points ',
                      datetime.datetime.fromtimestamp(current.created_utc), ' #' + current.id)
                comment_body_lines = current.body.splitlines()
                for line in comment_body_lines:
                    print(indent_string + line)
            except AttributeError:
                print(indent_string + 'deleted/removed', ' #' + current.id)
            print(indent_string)

        return True
