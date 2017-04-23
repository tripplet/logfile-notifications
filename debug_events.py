import tkinter as tk

servers = {
    1: 'testing/server1/test.log',
    2: 'testing/server2/test.log'
}


def event(server, login, user):
    with open(servers[server], 'at') as f:
        f.write('{} {}\n'.format('i' if login else 'o', user))

def user(root, name):
    user = tk.Frame(root)
    user.pack(side='left', padx=5, pady=10, ipadx=5, ipady=10)

    tk.Label(user, text=name).pack()
    tk.Button(user, text='Login Server 1', command=lambda: event(1, True, name)).pack()
    tk.Button(user, text='Logout Server 1', command=lambda: event(1, False, name)).pack()
    tk.Label(user).pack()
    tk.Button(user, text='Login Server 2', command=lambda: event(2, True, name)).pack()
    tk.Button(user, text='Logout Server 2', command=lambda: event(2, False, name)).pack()

root = tk.Tk()
root.title("LogfileNotifcations tests")
user(root, 'alice')
user(root, 'bob')
user(root, 'kyle')

#root.QUIT = tk.Button(root, text="QUIT", fg='red', command=root.destroy).pack(side="bottom")

root.lift()
root.attributes('-topmost',True)
root.after_idle(root.attributes,'-topmost',False)
root.mainloop()