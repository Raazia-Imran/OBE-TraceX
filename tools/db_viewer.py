"""Local, read-only SQLite inspection. No password hashes or MFA secrets are displayed."""
import sqlite3
import tkinter as tk
from tkinter import ttk
from pathlib import Path
root=tk.Tk();root.title('OBE-TraceX · Read-only database viewer');root.geometry('1150x640')
path=Path(__file__).resolve().parent.parent/'local.sqlite3'
connection=sqlite3.connect('file:'+path.as_posix()+'?mode=ro',uri=True)
queries={
 'Accounts (no passwords)': 'select u.username,u.email,p.role,u.is_active from auth_user u join evaluations_profile p on p.user_id=u.id',
 'Groups':'select id,project_id,title,expected_members,version from evaluations_projectgroup',
 'Students':'select id,seat,name,group_id from evaluations_student',
 'Master imports':'select id,student_id,synced_at,errors from evaluations_masterrecord',
 'Frozen approvals':'select id,group_id,stage,version,active,created_at from evaluations_frozenresult',
 'Audit history':'select id,action,target,at from evaluations_auditevent order by id desc limit 200'}
choice=tk.StringVar(value=list(queries)[0]);ttk.Label(root,text=str(path)+' — read-only',padding=12).pack(anchor='w')
combo=ttk.Combobox(root,textvariable=choice,values=list(queries),state='readonly');combo.pack(fill='x',padx=12,pady=8)
frame=ttk.Frame(root);frame.pack(expand=True,fill='both',padx=12,pady=12)
tree=ttk.Treeview(frame,show='headings');tree.pack(expand=True,fill='both')
def load(*args):
 cursor=connection.execute(queries[choice.get()]);cols=[x[0] for x in cursor.description]
 tree.delete(*tree.get_children());tree['columns']=cols
 for col in cols:tree.heading(col,text=col);tree.column(col,width=160,stretch=True)
 for row in cursor.fetchall():tree.insert('',tk.END,values=[str(x)[:500] for x in row])
combo.bind('<<ComboboxSelected>>',load);ttk.Button(root,text='Refresh',command=load).pack(pady=8);load();root.mainloop()
