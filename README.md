# Założenie

Ten bot służy do rozgrywek na serwerze "Nie daj się zbanować".
Zasady tego serwera są bardzo proste - gracze mają za zadanie
unikać łamania zasad, które są niejawne i zebrać przy tym jak
największą ilość punktów.

# Działanie

## Zasady

Zasady składają się z 3 elementów - typu zasady, listy regexów oraz listy akcji.

Typ akcji określa w jaki sposób zasada może zostać złamana,
poniższa lista zawiera wszystkie typy akcji:

- `MESSAGE` - jeśli wiadomość lub nazwa załącznika wysłanego 
przez użytkownika zawiera dany regex

- `ACTIVITY` - jeśli nazwa aktywności użytkownika zawiera dany regex

- `REACTION` - jeśli reakcja dodana do wiadomości zawiera dany regex

- `NAME` - jeśli nazwa użytkownika zawiera dany regex

- `POINTS_LESS_THAN` - jeśli użytkownik zawiera mniej niż X punktów

- `POINTS_GREATER_THAN` - jeśli użytkownik posiada więcej niż X punktów

- `ROLE` - jeśli użytkownik ma daną rolę i jego wiadomość zawiera regex

- `LAST_ACTIVITY` - jeśli ostatnia aktywność użytkownika była X czasu temu

Lista regexów powinna zawierać regexy działające z językiem 
Python, dla niektórych typów zasad w tej liście trzymane są argumenty

Lista akcji zawiera numery id akcji, które mają zostać wykonane po złamaniu zasady

## Akcje

Akcje, podobnie do zasad, składają się z typu akcji, 
argumentów or opcjonalnie z celów. To jak lista argumentów
i celów jest interpretowana zależy od typu akcji:

- `SEND_MESSAGE` - wysyła wiadomość o treści argumentu 0.
Domyślnie wiadomość zostanie wysłana na kanał na którym złamano
zasadę. Jeśli takiego nie ma, to wiadomość zostanie wysłana na 
domyślny kanał. W liście celów można zawrzeć listę kanałów
na które zostaną wysłane wiadomości o podanej treści.

- `DELETE_MESSAGE` - usuwa wiadomość, która złamała zasadę

- `KICK` - wyrzuca gracza z serwera. Można kickować
specyficznego gracza.

- `TIMEOUT` - wysyła gracza na przerwę, czas podawany jest w 
sekundach. Można timeoutować specyficznego gracza.

- `BAN` - banuje gracza dając mu rolę "Zbanowanego".
Można zbanować specyficznego gracza.

- `GIVE_ROLE` - daje graczowi daną role

- `REMOVE_ROLE` - zabiera graczowi daną rolę

- `CHANGE_NAME` - zmienia pseudonim gracza

- `ADD_POINTS` - dodaje graczowi daną ilość punktów. 
Liczba punktów może być ujemna

- `POLL` - rozpoczyna głosowanie na kanale, na którym została
złamana zasada lub na domyślnym kanale. Jesli głosowanie
uzyska większość głosów, na graczu wykonane zostanie wykonana
określona akcja o numerze arumentu 0. W argumencie 1 można
usytalić długość głosowania w sekundach. Na liście celów
można ustalić kanał, na którym odbędzie się głosowanie

- `RANDOM` - wykonuje losowo jedną z akcji z listy argumentów.

- `CHAIN` - wykonuje po kolei akcje z listy argumentów.
