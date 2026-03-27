# nRF PWM Tester & Motor Control

## Sprzęt:
- **Mikrokontroler:** Seeed Xiao nRF52840
- **Sterownik:** Adafruit 5648
- **Silnik wibracyjny:** MT58 (3V)

## Pinout:
| Sterownik MOSFET | Seeed Xiao|
| :--- | :--- |
| `IN` | `D0`(PWM) |
| `V+` | `5V` |
| `GND` | `GND` |

## Schemat połączeń:
<img width="1458" height="698" alt="obraz" src="https://github.com/user-attachments/assets/5edeac73-84c6-4150-8745-f924ae9c7c59" />
(połączenie bez złącza JST PH 3-pin)

## Instrukcja uruchomienia:
1. Build
2. Podłączyć nRF, zrestartować (kliknać dwa razy RST)
3. W terminalu nRF Connect: `west flash -r uf2`
4. Uruchomić aplikacje
5. **Zaznaczyć `Max 3V` dla MT58 !**

## Okno aplikacji:
<img width="592" height="355" alt="image" src="https://github.com/user-attachments/assets/bcad4212-90d0-4a0c-89df-acdb37d3b001" />

