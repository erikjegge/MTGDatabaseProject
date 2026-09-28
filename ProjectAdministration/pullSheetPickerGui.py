'''
    Really simple GUI wrapper around pullSheetPicker.py, for anyone who doesn't want
    to deal with a command line: pick the pull sheet CSV from a file browser, click
    Run, and it writes an Excel pick list next to the CSV.

    Launch by double-clicking RunPullSheetPicker.bat, or:
        pythonw pullSheetPickerGui.py
'''
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import pullSheetPicker as psp


class PullSheetPickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('MTG Pull Sheet Picker')
        self.root.geometry('640x460')
        self.root.minsize(560, 380)

        self.selected_path = tk.StringVar()
        self.status_queue = queue.Queue()
        self.last_output_path = None

        self._build_widgets()
        self._poll_status_queue()

    def _build_widgets(self):
        pad = {'padx': 10, 'pady': 6}

        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill='x', **pad)
        ttk.Label(file_frame, text='Pull sheet CSV:').pack(side='left')
        ttk.Entry(file_frame, textvariable=self.selected_path, state='readonly').pack(
            side='left', fill='x', expand=True, padx=(8, 8))
        ttk.Button(file_frame, text='Browse...', command=self._browse).pack(side='left')

        self.run_button = ttk.Button(self.root, text='Run', command=self._run_clicked, state='disabled')
        self.run_button.pack(**pad)

        self.log_box = scrolledtext.ScrolledText(self.root, height=16, state='disabled', wrap='word')
        self.log_box.pack(fill='both', expand=True, padx=10, pady=(0, 6))

        result_frame = ttk.Frame(self.root)
        result_frame.pack(fill='x', padx=10, pady=(0, 10))
        self.open_file_button = ttk.Button(
            result_frame, text='Open Pick List', command=self._open_output, state='disabled')
        self.open_file_button.pack(side='left')
        self.open_folder_button = ttk.Button(
            result_frame, text='Open Folder', command=self._open_folder, state='disabled')
        self.open_folder_button.pack(side='left', padx=(8, 0))

    def _browse(self):
        path = filedialog.askopenfilename(
            title='Select TCGplayer pull sheet',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
        )
        if path:
            self.selected_path.set(path)
            self.run_button['state'] = 'normal'

    def _log(self, message):
        self.log_box['state'] = 'normal'
        self.log_box.insert('end', message + '\n')
        self.log_box.see('end')
        self.log_box['state'] = 'disabled'

    def _run_clicked(self):
        path = self.selected_path.get()
        if not path:
            return

        self.log_box['state'] = 'normal'
        self.log_box.delete('1.0', 'end')
        self.log_box['state'] = 'disabled'
        self.run_button['state'] = 'disabled'
        self.open_file_button['state'] = 'disabled'
        self.open_folder_button['state'] = 'disabled'
        self.last_output_path = None

        thread = threading.Thread(target=self._run_worker, args=(path,), daemon=True)
        thread.start()

    def _run_worker(self, path):
        try:
            summary = psp.process_pull_sheet(
                path, psp.DEFAULT_BOX_CODE, progress_cb=lambda msg: self.status_queue.put(('log', msg)))
            self.status_queue.put(('summary', summary))
        except Exception as e:
            self.status_queue.put(('error', str(e)))

    def _poll_status_queue(self):
        try:
            while True:
                kind, payload = self.status_queue.get_nowait()
                if kind == 'log':
                    self._log(payload)
                elif kind == 'error':
                    self._log(f'ERROR: {payload}')
                    self.run_button['state'] = 'normal'
                    messagebox.showerror('Failed', payload)
                elif kind == 'summary':
                    self._show_summary(payload)
        except queue.Empty:
            pass
        self.root.after(150, self._poll_status_queue)

    def _show_summary(self, summary):
        self._log('')
        self._log(f"Cards ordered (all lines): {summary['total_ordered']}")
        self._log(f"Cards matched and ready to pull: {summary['matched_count']}")
        self._log(f"Order lines not found in box {summary['box_code']}: {summary['not_found_count']}")
        self._log(f"Order lines needing manual review: {summary['needs_review_count']}")
        self._log(f"TCGplayer set names with no exact match in your set library: {summary['set_mismatch_count']}")
        self._log('')
        self._log('\n'.join(psp.render_problem_section('NOT FOUND IN BOX', summary['not_found'], psp.render_not_found)))
        self._log('\n'.join(psp.render_problem_section('NEEDS MANUAL REVIEW', summary['needs_review'], psp.render_needs_review)))
        self._log('')
        self._log(f"Pick list written to: {summary['output_path']}")

        self.last_output_path = summary['output_path']
        self.run_button['state'] = 'normal'
        self.open_file_button['state'] = 'normal'
        self.open_folder_button['state'] = 'normal'

    def _open_output(self):
        if self.last_output_path and os.path.exists(self.last_output_path):
            os.startfile(self.last_output_path)

    def _open_folder(self):
        if self.last_output_path:
            os.startfile(os.path.dirname(os.path.abspath(self.last_output_path)))


def main():
    root = tk.Tk()
    PullSheetPickerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
