🟦 Game 2: MATRIX PONG
Location: Matrix Room
🎮 Introduction
Matrix Pong aduce clasicul joc arcade în realitate pe o grilă LED de 16 x 32. Nu este doar un joc de reflexe, ci și unul de mișcare fizică, unde jucătorii își controlează paleta prin poziționarea lor pe grid-ul interactiv de la podea.

🕹️ Gameplay mechanics
Jocul este o competiție Versus 1 la 1 (sau echipe), fără nivele, bazată pe puncte.

Fileul (Paleta): Fiecare jucător controlează un "fileu" format din 8 segmente (pătrate).

Control prin Mișcare: Jucătorul trebuie să stea fizic pe ultimul pătrat al paletei sale. Dacă face un pas înainte (sus) sau înapoi (jos) pe coloana sa, întreaga paletă se deplasează în acea direcție.

Mingea: Reprezentată de un pătrat luminos care se mișcă folosind vectori de viteză. La începutul meciului, mingea pleacă întotdeauna către Jucătorul 1.

Gravitație Simulată: Traiectoria mingii tinde să aibă o ușoară deviere pe axa verticală (simulând o formă de gravitație prin vectori) pentru a face mișcarea imprevizibilă.

Delimitarea: Terenul este împărțit de o linie punctată centrală.

Coliziuni: * Mingea ricoșează din marginile de sus și de jos.

Dacă mingea atinge marginile laterale în spatele paletei, jucătorul respectiv pierde punctul.

🔊 Audio & Visual Feedback
Collision Sound: Sunet de impact la lovirea paletei.

Fail Sound: Sunet de eșec (void) când se ratează mingea.

Game Over: Semnal sonor la atingerea limitei de puncte (11 sau 21).

Visual Win/Loss: La final, jumătatea câștigătorului devine VERDE (Winner), iar cea a pierzătorului devine ROȘIE (Loser).

⚙️ Configuration
Runde: Meciul se poate juca în sistem "Best of" (1, 3 sau 5 runde).

Scor de câștig: Limita de puncte per rundă (11 sau 21).

Personalizare: Jucătorii pot alege culoarea paletei lor înainte de start.

Control: Funcții de Reset / Restart și Pause disponibile pe touchscreen-ul de control.

💎 LedHack Bonus Points Checklist (Implemented)
[x] Smart Hardware Usage: Controlul paletei în Pong prin poziționarea fizică a jucătorului.

[x] Sound Implementation: Feedback audio dinamic pentru acțiuni (lovituri, gol, win/loss).

[x] Configurability: Opțiuni multiple pentru runde, scor și culori.

[x] Onboarding: Ecrane de tutorial incluse înainte de "Mission Start".