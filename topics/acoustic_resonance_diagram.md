```mermaid
graph TB
    subgraph Эксперимент["🔬 ЭКСПЕРИМЕНТ: Акустический резонанс"]
        T[Труба с пенопластовыми шариками]
        A[Акустический сигнал частоты f]
        SW[Стоячая волна]
        T --> SW
        A --> SW
    end

    subgraph Классическая["❌ КЛАССИЧЕСКАЯ ТЕОРИЯ (ошибочная)"]
        CH[Хаотическое движение молекул]
        R[Случайные столкновения]
        P1[Давление = удары о стенки]
        CH --> R --> P1
        style CH fill:#ffcccc
        style R fill:#ffcccc
        style P1 fill:#ffcccc
    end

    subgraph Baziev["✅ ТЕОРИЯ БАЗИЕВА (правильная)"]
        O[Осцилляторы - молекулы газа]
        HF[Гиперчастотные колебания]
        G[Глобулы - элементарные объемы]
        UP[Упорядоченное движение]
        E[E = h·ν]
        P2[P = E/V₀ - концентрация энергии]
        
        O --> HF
        HF --> G
        G --> UP
        UP --> E
        E --> P2
        
        style O fill:#ccffcc
        style HF fill:#ccffcc
        style G fill:#ccffcc
        style UP fill:#ccffcc
        style E fill:#ccffcc
        style P2 fill:#ccffcc
    end

    subgraph Mechanism["🎯 МЕХАНИЗМ ОБРАЗОВАНИЯ СТОЛБИКОВ"]
        direction TB
        N1[Узел: амплитуда min]
        Pu1[Пучность: амплитуда MAX]
        N2[Узел: амплитуда min]
        Pu2[Пучность: амплитуда MAX]
        N3[Узел: амплитуда min]
        
        Pr1[Давление низкое]
        Pr2[Давление ВЫСОКОЕ]
        Pr3[Давление низкое]
        Pr4[Давление ВЫСОКОЕ]
        Pr5[Давление низкое]
        
        B1[💨 Шарики отталкиваются]
        B2[📍 Шарики собираются в СТОЛБИК]
        B3[💨 Шарики отталкиваются]
        B4[📍 Шарики собираются в СТОЛБИК]
        B5[💨 Шарики отталкиваются]
        
        N1 --> Pr1 --> B1
        Pu1 --> Pr2 --> B2
        N2 --> Pr3 --> B3
        Pu2 --> Pr4 --> B4
        N3 --> Pr5 --> B5
        
        style Pu1 fill:#ffff99
        style Pu2 fill:#ffff99
        style Pr2 fill:#ff9999
        style Pr4 fill:#ff9999
        style B2 fill:#99ff99
        style B4 fill:#99ff99
    end

    subgraph Formulas["📐 КЛЮЧЕВЫЕ ФОРМУЛЫ"]
        F1["Энергия осциллятора:<br/>E = h·ν"]
        F2["Давление в глобуле:<br/>P₀ = h·ν / V₀"]
        F3["Скорость молекулы:<br/>v = √(h·ν / m)"]
        F4["НЕ v = √(3kT/m) !"]
        
        F1 --> F2 --> F3
        F3 -.отличается от.-> F4
        
        style F1 fill:#cce5ff
        style F2 fill:#cce5ff
        style F3 fill:#cce5ff
        style F4 fill:#ffcccc
    end

    SW --> Mechanism
    Baziev --> Mechanism
    Baziev --> Formulas
    
    Mechanism --> Result["🎊 РЕЗУЛЬТАТ:<br/>Упорядоченные столбики<br/>в пучностях"]
    
    style Result fill:#90EE90,stroke:#333,stroke-width:4px

    Note1["💡 ДОКАЗАТЕЛЬСТВО:<br/>Газ имеет СТРУКТУРУ,<br/>молекулы движутся УПОРЯДОЧЕННО,<br/>а не хаотично!"]
    
    Result --> Note1
    
    style Note1 fill:#FFD700,stroke:#FF0000,stroke-width:3px
```

# Схема взаимодействия молекул в акустическом поле

## Стоячая волна и распределение глобул

```mermaid
graph LR
    subgraph Zone1["Узел 1"]
        M1_1((м))
        M1_2((м))
        M1_3((м))
        style M1_1 fill:#e0e0e0
        style M1_2 fill:#e0e0e0
        style M1_3 fill:#e0e0e0
    end
    
    subgraph Zone2["Пучность 1 - СТОЛБИК"]
        M2_1((М))
        M2_2((М))
        M2_3((М))
        M2_4((М))
        M2_5((М))
        S1[🟡]
        S2[🟡]
        S3[🟡]
        style M2_1 fill:#ff6666
        style M2_2 fill:#ff6666
        style M2_3 fill:#ff6666
        style M2_4 fill:#ff6666
        style M2_5 fill:#ff6666
        style S1 fill:#ffff00
        style S2 fill:#ffff00
        style S3 fill:#ffff00
    end
    
    subgraph Zone3["Узел 2"]
        M3_1((м))
        M3_2((м))
        M3_3((м))
        style M3_1 fill:#e0e0e0
        style M3_2 fill:#e0e0e0
        style M3_3 fill:#e0e0e0
    end
    
    subgraph Zone4["Пучность 2 - СТОЛБИК"]
        M4_1((М))
        M4_2((М))
        M4_3((М))
        M4_4((М))
        M4_5((М))
        S4[🟡]
        S5[🟡]
        S6[🟡]
        style M4_1 fill:#ff6666
        style M4_2 fill:#ff6666
        style M4_3 fill:#ff6666
        style M4_4 fill:#ff6666
        style M4_5 fill:#ff6666
        style S4 fill:#ffff00
        style S5 fill:#ffff00
        style S6 fill:#ffff00
    end
    
    Zone1 -->|λ/4| Zone2
    Zone2 -->|λ/4| Zone3
    Zone3 -->|λ/4| Zone4
    
    P1["P низкое<br/>E/V₀ мало"]
    P2["P ВЫСОКОЕ<br/>E/V₀ велико"]
    P3["P низкое<br/>E/V₀ мало"]
    P4["P ВЫСОКОЕ<br/>E/V₀ велико"]
    
    Zone1 -.-> P1
    Zone2 -.-> P2
    Zone3 -.-> P3
    Zone4 -.-> P4
    
    style P1 fill:#ccccff
    style P2 fill:#ff9999
    style P3 fill:#ccccff
    style P4 fill:#ff9999
```

Легенда:
- (м) - молекула с малой амплитудой колебаний (узел)
- (М) - молекула с большой амплитудой колебаний (пучность)
- 🟡 - пенопластовый шарик
- λ - длина волны
