import webbrowser

import PySimpleGUI as sg

from search_engine import SearchEngine


class SearchEngineGUI:
    sg.theme('DefaultNoMoreNagging')
    query = ""
    methods = ['BERT', "TFIDF"]

    def __init__(self, method="TFIDF"):
        self.method = method
        try:
            self.engine = SearchEngine(method=method)
        except Exception as e:
            self.engine = SearchEngine(fresh_start=True, method=method)

    def get_main_layout(self):
        main_layout = [[sg.Text('Search Engine', justification='center', size=(70, 1))],
                       [sg.Text(" ", justification='left', size=(20, 1))],
                       [sg.Text('Enter Query:'),
                        sg.Input(justification='left', size=(50, 1)),
                        sg.Button('Go', size=(10, 1), bind_return_key=True)],
                       [sg.Text(" ", justification='left', size=(20, 1))],
                       [sg.Text(" ", justification='left', size=(20, 1)),
                        sg.Button('Exit', size=(20, 1))]
                       ]
        return main_layout

    def get_results_layout(self, results, num_results):
        selection = [10, 50, 100]
        i = 0
        results_layout = [[sg.Text("Results",
                                   justification='center',
                                   size=(100, 2),
                                   text_color='#FFFFFF',
                                   background_color='#0645AD',
                                   enable_events=True,
                                   pad=(0, 10)),
                           sg.Combo(selection, enable_events=True, key='combo', background_color='#0645AD'),
                           sg.Button('Go')]]
        result_items = []
        for title, link in results:
            i += 1
            if i > num_results:
                break
            title_Text = sg.Text(title, justification='left', size=(100, 1), pad=(50, 0))
            link_Text = sg.Text(link,
                                text_color="#0645AD",
                                justification='left',
                                size=(100, 1),
                                enable_events=True,
                                pad=(50, 0))
            padding_b = sg.Text("-" * 100, justification='left', size=(100, 1), enable_events=True, pad=(50, 5))
            result_items += [[title_Text], [link_Text], [padding_b]]
        results_layout.append([sg.Column(result_items, size=(500, 400), scrollable=True, justification='center')])
        results_layout.append([sg.Text(" ", justification='left', size=(35, 1)),
                               sg.Button('Exit', size=(20, 1)),
                               sg.Button('Back', size=(20, 1))])
        return results_layout

    def start_main(self):
        main_layout = self.get_main_layout()
        window = sg.Window('Information Retrieval', icon='uic_logo.ico').layout(main_layout)
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == 'Exit':
                window.close()
                break
            if values:
                self.query = values[0]
            if event == 'Go':
                window.close()
                if self.query:
                    self.start_results()
                    break
                else:
                    sg.popup(f"Query Empty")
                    self.start_main()

    def start_results(self, results=None, num_results=10):
        if results is None:
            results = self.get_results()
        if not results:
            sg.popup("No Results Found")
            self.start_main()
            return
        links = [res[1] for res in results]
        results_layout = self.get_results_layout(results, num_results=num_results)
        window = sg.Window('Information Retrieval', icon='uic_logo.ico').layout(results_layout)
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == 'Exit':
                window.close()
                break
            if event == 'Back':
                window.close()
                self.start_main()
                break
            elif event in links:
                self.launch_browser(event)
            elif event == 'Go':
                _num_results = int(values['combo'])
                window.close()
                self.start_results(results=results, num_results=_num_results)

    def get_results(self):
        print(self.query)
        return self.engine.search(self.query)

    def launch_browser(self, url):
        webbrowser.open(url, new=2)


def main():
    gui = SearchEngineGUI()
    gui.start_main()


if __name__ == '__main__':
    main()
