# nRF PWM Tester & Motor Control

## Sprzęt:
- **Mikrokontroler:** Seeed Xiao nRF52840
- **Sterownik:** Adafruit 5648 

## Pinout:
| Sterownik MOSFET | Seeed Xiao|
| :--- | :--- |
| `IN` | `D0`(PWM) |
| `V+` | `5V` |
| `GND` | `GND` |


## Instrukcja uruchomienia:
1. Build
2. Podłączyć nRF, zrestartować (kliknać dwa razy RST)
3. W terminalu nRF Connect: `west flash -r uf2`
4. Uruchomić aplikacje 

<img width="592" height="355" alt="image" src="https://github.com/user-attachments/assets/bcad4212-90d0-4a0c-89df-acdb37d3b001" />
