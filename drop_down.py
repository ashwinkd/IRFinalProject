import PySimpleGUI as sg

layout = [[sg.Combo(['choice 1', 'choice 2', 'choice 3'], enable_events=True, key='combo')],
          [sg.Button('Test'), sg.Exit()]
          ]

window = sg.Window('combo test', layout)

while True:
    event, values = window.Read()
    if event is None or event == 'Exit':
        break

    if event == 'Test':
        combo = values['combo']  # use the combo key
        print(combo)

window.Close()