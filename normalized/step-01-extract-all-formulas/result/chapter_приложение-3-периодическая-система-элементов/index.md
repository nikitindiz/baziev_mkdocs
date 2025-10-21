# Приложение 3. Периодическая система элементов Д. И. Менделеева, составленная по наиболее распространенным в природе изотопам, без усреднения, по данным на 1983 г.

<style>
  table.periodic {
    border-collapse: collapse;
    border: 1px solid black;
    font-family: sans-serif;
    font-size: 10px; /* Adjusted for better fit */
    text-align: center;
  }
  
  table.periodic td {
    border: 1px solid black;
    padding: 4px;
    vertical-align: top; /* Align content to the top */
    /* width: 100%; */
    width: calc(100%/9);
  }
  table.periodic th {
    background-color: #f2f2f2;
    font-weight: bold;
  }

  table.periodic tr {
    width: 100%;
  }

  table.periodic tr th:nth-child(1) {
    width: 10%;
  }

  /* Style for element symbol */
  table.periodic .symbol {
    font-size: 14px;
    font-weight: bold;
    display: block; /* Make symbol appear on its own line */
    margin-bottom: 2px;
  }
  /* Style for atomic number */
  table.periodic .atomic-number {
    font-size: 9px;
    display: block; /* On its own line */
    margin-bottom: 2px;
  }
   /* Style for name */
  table.periodic .name {
    font-size: 9px;
    display: block; /* On its own line */
    margin-bottom: 2px;
   }
  /* Style for atomic mass */
  table.periodic .mass {
    font-size: 9px;
    display: block; /* On its own line */
  }
  /* Style for the top number (often mass number) shown in image */
  table.periodic .mass-number {
      position: absolute; /* Allows positioning */
      top: 2px; /* Adjust as needed */
      right: 2px; /* Adjust as needed */
      font-size: 9px;
  }
   table.periodic td {
       position: relative; /* Needed for absolute positioning of mass number */
   }
    /* Simplify representation within cell for Markdown compatibility */
    /* Format: AtomicNumber<br>Symbol<br>Name<br>Mass */
</style>

Каждая ячейка содержит:
* _H_ - Символ и его подгруппа
* _1_ - Атомное число
* _1,0078_ - Атомная масса
* _Водород_ - Название

<table class="periodic">
  <thead>
    <tr>
      <th rowspan="2">Периоды</th>
      <th colspan="9">Группы</th>
    </tr>
    <tr>
      <th>I</th>
      <th>II</th>
      <th>III</th>
      <th>IV</th>
      <th>V</th>
      <th>VI</th>
      <th>VII</th>
      <th>VIII</th>
      <th>IX</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>1</th>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td></td>
      <td> 
        1<br><span class="symbol">H</span>Водород<br>1,0078<br><br>
        2<br><span class="symbol">D</span>Дейтерий<br>2,0141<br><br>
        3<br><span class="symbol">T</span>Тритий<br>3,016997
      </td>
      <td>4<br><span class="symbol">He</span>Гелий<br>4,0026</td>
    </tr>
    <tr>
      <th>2</th>
      <td>5<br><span class="symbol">Li</span>Литий<br>7,0160</td>
      <td>6<br><span class="symbol">Be</span>Бериллий<br>9,0122</td>
      <td>7<br><span class="symbol">B</span>Бор<br>11,0093</td>
      <td>8<br><span class="symbol">C</span>Углерод<br>12,0000</td>
      <td>9<br><span class="symbol">N</span>Азот<br>14,0031</td>
      <td>10<br><span class="symbol">O</span>Кислород<br>15,999415</td>
      <td>11<br><span class="symbol">F</span>Фтор<br>18,998403</td>
      <td></td>
      <td>12<br><span class="symbol">Ne</span>Неон<br>19,9924</td>
    </tr>
    <tr>
      <th>3</th>
      <td>13<br><span class="symbol">Na</span>Натрий<br>22,9898</td>
      <td>14<br><span class="symbol">Mg</span>Магний<br>23,9850</td>
      <td>15<br><span class="symbol">Al</span>Алюминий<br>26,9815</td>
      <td>16<br><span class="symbol">Si</span>Кремний<br>27,9769</td>
      <td>17<br><span class="symbol">P</span>Фосфор<br>30,9738</td>
      <td>18<br><span class="symbol">S</span>Сера<br>31,9721</td>
      <td>19<br><span class="symbol">Cl</span>Хлор<br>34,9688</td>
      <td></td>
      <td>20<br><span class="symbol">Ar</span>Аргон<br>39,9624</td>
    </tr>
    <tr>
      <th>4</th>
      <td>
        21<br><span class="symbol">K</span>Калий<br>38,9637<br><br>
        31<br><span class="symbol">Cu</span>Медь<br>62,9298
      </td>
      <td>
        22<br><span class="symbol">Ca</span>Кальций<br>39,9626<br><br>
        32<br><span class="symbol">Zn</span>Цинк<br>63,9291
      </td>
      <td>23<br><span class="symbol">Sc</span>Скандий<br>44,9559<br><br>
        33<br><span class="symbol">Ga</span>Галлий<br>68,9257
      </td>
      <td>24<br><span class="symbol">Ti</span>Титан<br>47,9479<br><br>
        34<br><span class="symbol">Ge</span>Германий<br>73,9219
      </td>
      <td>25<br><span class="symbol">V</span>Ванадий<br>50,9440<br><br>
        35<br><span class="symbol">As</span>Мышьяк<br>74,9216
      </td>
      <td>26<br><span class="symbol">Cr</span>Хром<br>51,9405<br><br>
        36<br><span class="symbol">Se</span>Селен<br>79,9165
      </td>
      <td>27<br><span class="symbol">Mn</span>Марганец<br>54,9380<br><br>
        37<br><span class="symbol">Br</span>Бром<br>78,9183
      </td>
      <td>
        28<br><span class="symbol">Fe</span>Железо<br>55,9349<br><br>
        29<br><span class="symbol">Ni</span>Никель<br>57,9353<br><br>
        30<br><span class="symbol">Co</span>Кобальт<br>58,9332
      </td>
      <td>38<br><span class="symbol">Kr</span>Криптон<br>83,9115</td>
    </tr>
    <tr>
      <th>5</th>
      <td>
        39<br><span class="symbol">Rb</span>Рубидий<br>84,9117<br><br>
        49<br><span class="symbol">Ag</span>Серебро<br>106,9051
      </td>
      <td>
        40<br><span class="symbol">Sr</span>Стронций<br>87,9056<br><br>
        50<br><span class="symbol">Cd</span>Кадмий<br>113,9034
      </td>
      <td>41<br><span class="symbol">Y</span>Иттрий<br>88,9059<br><br>
        51<br><span class="symbol">In</span>Индий<br>114,9039
      </td>
      <td>42<br><span class="symbol">Zr</span>Цирконий<br>89,9047<br><br>
        52<br><span class="symbol">Sn</span>Олово<br>119,9022
      </td>
      <td>43<br><span class="symbol">Nb</span>Ниобий<br>92,9064<br><br>
        53<br><span class="symbol">Sb</span>Сурьма<br>120,9038
      </td>
      <td>44<br><span class="symbol">Mo</span>Молибден<br>97,9054<br><br>
        54<br><span class="symbol">Te</span>Теллур<br>129,9062
      </td>
      <td>45<br><span class="symbol">Tc</span>Технеций<br>97,9072<br><br>
        55<br><span class="symbol">I</span>Йод<br>126,9045
      </td>
      <td>
        46<br><span class="symbol">Ru</span>Рутений<br>101,9056<br><br>
        47<br><span class="symbol">Rh</span>Родий<br>102,9055<br><br>
        48<br><span class="symbol">Pd</span>Палладий<br>105,9035
      </td>
      <td>56<br><span class="symbol">Xe</span>Ксенон<br>131,9041</td>
    </tr>
    <tr>
      <th>6</th>
      <td>
        57<br><span class="symbol">Cs</span>Цезий<br>132,9054<br><br>
        81<br><span class="symbol">Au</span>Золото<br>196,9665
      </td>
      <td>
        58<br><span class="symbol">Ba</span>Барий<br>137,9052<br><br>
        82<br><span class="symbol">Hg</span>Ртуть<br>201,9706
      </td>
      <td>59<br><span class="symbol">La</span>Лантан<br>138,9064<br><br>
        83<br><span class="symbol">Tl</span>Таллий<br>204,9744
      </td>
      <td>74<br><span class="symbol">Hf</span>Гафний<br>179,9466<br><br>
        84<br><span class="symbol">Pb</span>Свинец<br>207,9766
      </td>
      <td>75<br><span class="symbol">Ta</span>Тантал<br>180,9480<br><br>
        85<br><span class="symbol">Bi</span>Висмут<br>208,9804
      </td>
      <td>76<br><span class="symbol">W</span>Вольфрам<br>183,9540<br><br>
        86<br><span class="symbol">Po</span>Полоний<br>[209]
      </td>
      <td>77<br><span class="symbol">Re</span>Рений<br>186,9558<br><br>
        87<br><span class="symbol">At</span>Астат<br>[210]
      </td>
      <td>
        78<br><span class="symbol">Os</span>Осмий<br>191,9615<br><br>
        79<br><span class="symbol">Ir</span>Иридий<br>192,9629<br><br>
        80<br><span class="symbol">Pt</span>Платина<br>194,9648
      </td>
      <td>88<br><span class="symbol">Rn</span>Радон<br>[222]</td>
    </tr>
    <tr>
      <th>7</th>
      <td>89<br><span class="symbol">Fr</span>Франций<br>[223]</td>
      <td>90<br><span class="symbol">Ra</span>Радий<br>[226]</td>
      <td>91<br><span class="symbol">Ac</span>Актиний<br>[227]</td>
      <td>92<br><span class="symbol">Th</span>Торий<br>232,0381</td>
      <td>93<br><span class="symbol">Pa</span>Протактиний<br>[231]</td>
      <td>94<br><span class="symbol">U</span>Уран<br>238,0508</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table> Приложение 3 (продолжение) Лантаноиды

<style>
  table.lantanoids {
    border-collapse: collapse;
    border: 1px solid black;
    font-family: sans-serif;
    font-size: 10px; /* Adjusted for better fit */
    text-align: center;
  }
  table.lantanoids th, td {
    border: 1px solid black;
    padding: 4px;
    vertical-align: middle; /* Center content vertically */
    height: 50px; /* Approximate height */
    width: 80px; /* Approximate width */
  }
  /* Style for element symbol */
  table.lantanoids .symbol {
    font-size: 14px;
    font-weight: bold;
  }
  /* Minimal styles for markdown */
</style>

<table class="lantanoids">
  <tbody>
    <tr>
      <td>
        <span class="symbol">Ce</span> 140<br>
        139,9054<br>
        60 Церий
      </td>
      <td>
        <span class="symbol">Pr</span> 141<br>
        140,9077<br>
        61 Празеодим
      </td>
      <td>
        <span class="symbol">Nd</span> 142<br>
        141,9077<br>
        62 Неодим
      </td>
      <td>
        <span class="symbol">Pm</span> 145<br>
        144,9128<br>
        63 Прометий
      </td>
    </tr>
    <tr>
      <td>
        <span class="symbol">Sm</span> 152<br>
        151,9197<br>
        64 Самарий
      </td>
      <td>
        <span class="symbol">Eu</span> 153<br>
        152,9212<br>
        65 Европий
      </td>
      <td>
        <span class="symbol">Gd</span> 158<br>
        157,9241<br>
        66 Гадолиний
      </td>
      <td>
        <span class="symbol">Tb</span> 159<br>
        158,9254<br>
        67 Тербий
      </td>
    </tr>
    <tr>
      <td>
        <span class="symbol">Dy</span> 164<br>
        163,9292<br>
        68 Диспрозий
      </td>
      <td>
        <span class="symbol">Ho</span> 165<br>
        164,9304<br>
        69 Гольмий
      </td>
      <td>
        <span class="symbol">Er</span> 166<br>
        165,9303<br>
        70 Эрбий
      </td>
      <td>
        <span class="symbol">Tm</span> 169<br>
        168,9342<br>
        71 Тулий
      </td>
    </tr>
    <tr>
      <td>
        <span class="symbol">Yb</span> 174<br>
        173,9389<br>
        72 Иттербий
      </td>
      <td>
        <span class="symbol">Lu</span> 175<br>
        174,9408<br>
        73 Лютеций
      </td>
      
      <td></td>
      <td></td>
    </tr>
  </tbody>
</table>



