# Формат `.newtrobat` — спецификация для нейросетей

> Проект: **NewCatroid** (форк Pocket Code / Catrobat)
> Репозиторий: https://github.com/Danveyd/NewCatroid
> Назначение файла: сохранённый проект блочного визуального программирования (аналог Scratch/Catrobat), включающий сцены, спрайты, скрипты (блоки), медиаресурсы и звук.

---

## 1. Общая идея

`.newtrobat` — это переименованный ZIP-архив (аналогично `.docx`, `.apk`, `.scratch3`). Чтобы прочитать проект, нужно:

1. Распаковать файл как обычный ZIP-архив.
2. Найти и распарсить `code.xml` — главный файл-описание программы.
3. Сопоставить пути к ресурсам (изображения, звуки), указанные в `code.xml`, с файлами внутри соответствующих папок сцен.

```
project.newtrobat  (это ZIP-архив)
```

---

## 2. Структура архива

```
project.newtrobat/
├── code.xml                  # Главный файл программы — описывает всю логику, сцены, объекты и блоки
├── files/                    # Произвольные пользовательские файлы проекта
│   ├── file.txt               # пример файла
│   └── ...                    # могут быть любые файлы и вложенные папки любой структуры
├── Сцена/                    # Папка сцены №1 (имя папки = имя сцены, задаётся пользователем/движком)
│   ├── images/                 # Изображения (фоны, спрайты/костюмы), используемые в этой сцене
│   └── sounds/                 # Звуковые файлы, используемые в этой сцене
├── Сцена 2/                  # Папка сцены №2 (если сцен несколько)
│   ├── images/
│   └── sounds/
└── ...                       # Дополнительные сцены по аналогии
```

### Ключевые правила структуры

- **`code.xml`** всегда лежит в корне архива и является единственным источником истины о логике проекта, наборе сцен, объектов и их ресурсов.
- **Папка(и) сцены** названы по имени сцены (то же значение, что в `code.xml` в `scenes/scene/name`). Для проекта с несколькими сценами — по одной папке на каждую сцену.
- Внутри папки сцены обязательны (при наличии соответствующих ресурсов) подпапки:
  - `images/` — статичные изображения: фоны (`look`), костюмы объектов.
  - `sounds/` — звуковые файлы, подключаемые через `soundList` объектов.
- **`files/`** — служебная/пользовательская директория произвольного назначения. Она НЕ участвует напрямую в логике блоков и может содержать что угодно: текстовые файлы, вложенные папки, дополнительные данные, экспортированные ресурсы и т.д. Формат и структура содержимого `files/` не регламентированы движком.
- Сцен может быть **0, 1 или множество** — количество определяется тегом `<scenes>` в `code.xml`, где каждая сцена — отдельный `<scene>`-элемент с уникальным `sceneId`.

---

## 3. Формат `code.xml`

`code.xml` — XML-документ, основанный на диалекте Catrobat Language (см. `<catrobatLanguageVersion>`). Кодировка — UTF-8.

### 3.1. Корневой элемент

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<program>
  <header>...</header>
  <settings/>
  <scenes>...</scenes>
  <programVariableList>...</programVariableList>
  <programListOfLists/>
  <programMultiplayerVariableList/>
  <disableScientificNotation>false</disableScientificNotation>
</program>
```

### 3.2. `<header>` — метаданные проекта

Содержит информацию о проекте и среде, в которой он создан/собран. Основные поля:

| Тег | Назначение |
|---|---|
| `applicationName` / `applicationVersion` | Название и версия приложения-редактора (например, `NewCatroid`, `2.2.0`) |
| `applicationBuildName/Number/Type` | Данные о сборке приложения |
| `catrobatLanguageVersion` | Версия языка блоков (влияет на набор доступных блоков/атрибутов) |
| `programName` | Имя проекта, отображаемое пользователю |
| `description`, `notesAndCredits`, `tags` | Текстовые метаданные проекта |
| `deviceName`, `platform`, `platformVersion` | Устройство и ОС, на которых собран проект (например, `Android`, API `36`) |
| `screenWidth`, `screenHeight`, `screenMode` | Разрешение и режим масштабирования сцены (`STRETCH` и др.) |
| `landscapeMode` | Ориентация экрана |
| `customResolution` | Признак нестандартного разрешения |
| `scenesEnabled` | Включена ли поддержка нескольких сцен |
| `isCastProject` | Признак специального типа проекта (например, для трансляции) |
| `physicsWidthArea`, `physicsHeightArea` | Размеры физического мира для симуляции физики |
| `programLicense`, `mediaLicense` | Лицензии кода и медиаресурсов |
| `remixOf`, `gitRemoteUrl`, `url` | Ссылки на источник/ремикс/репозиторий |
| `userHandle` | Имя пользователя-автора |
| `dateTimeUpload`, `listeningLanguageTag` | Служебные поля (дата загрузки, язык распознавания голоса) |

Большинство текстовых полей могут быть пустыми строками.

### 3.3. `<settings/>`

Глобальные настройки проекта (в примере — пусто). Может содержать переключатели поведения движка.

### 3.4. `<scenes>` — сцены проекта

```xml
<scenes>
  <scene sceneId="UUID">
    <name>Имя сцены</name>
    <objectList>
      <object type="Sprite" spriteId="UUID" name="Имя объекта">
        <lookList>...</lookList>
        <soundList>...</soundList>
        <scriptList>...</scriptList>
        <nfcTagList/>
        <userVariables/>
        <userLists/>
        <userDefinedBrickList/>
      </object>
    </objectList>
  </scene>
</scenes>
```

- Каждая `<scene>` имеет уникальный `sceneId` (UUID) и `<name>` — это имя должно совпадать с именем соответствующей папки сцены в архиве.
- `<objectList>` содержит все объекты (спрайты) сцены.

#### Объект (`<object>`)

| Атрибут/тег | Назначение |
|---|---|
| `type` | Тип объекта, обычно `Sprite` |
| `spriteId` | Уникальный UUID объекта |
| `name` | Имя объекта, видимое пользователю |
| `lookList` | Список внешних видов/костюмов объекта — каждый `<look>` ссылается на файл в `images/` |
| `soundList` | Список звуков объекта — каждый `<sound>` ссылается на файл в `sounds/` |
| `scriptList` | Список скриптов (программ), запускаемых на этом объекте |
| `nfcTagList` | NFC-метки, привязанные к объекту (специфика мобильной платформы) |
| `userVariables` / `userLists` | Локальные переменные и списки объекта |
| `userDefinedBrickList` | Пользовательские (кастомные) блоки, определённые для объекта |

#### `<look>` (внешний вид/костюм/фон)

```xml
<look fileName="Фон.png" lookId="UUID" name="Фон">
  <isWebRequest>false</isWebRequest>
  <valid>true</valid>
</look>
```

- `fileName` — имя файла изображения, которое нужно искать в `<Имя сцены>/images/`.
- `isWebRequest` — признак того, что ресурс загружается по сети, а не хранится локально.
- `valid` — флаг корректности/доступности ресурса.

Аналогично для `<sound>` внутри `soundList` — файл ищется в `<Имя сцены>/sounds/`.

#### `<scriptList>` и скрипты

```xml
<script type="StartScript" posX="0.0" posY="0.0">
  <brickList>
    <brick type="...">...</brick>
  </brickList>
  <commentedOut>false</commentedOut>
  <scriptId>UUID</scriptId>
</script>
```

- `type` — тип триггера скрипта (например, `StartScript` — запуск при старте проекта; возможны и другие триггеры: по нажатию, по получению сообщения, по столкновению и т.п. — зависит от версии языка).
- `posX`, `posY` — позиция блока-скрипта на визуальном холсте редактора (для отображения, не влияет на выполнение).
- `brickList` — упорядоченный список блоков (`<brick>`), которые выполняются последовательно сверху вниз.

#### `<brick>` — отдельный программный блок

Каждый `<brick>` — это один "кирпичик" визуального языка (аналог оператора/инструкции).

```xml
<brick type="SetVariableBrick">
  <brickId>UUID</brickId>
  <commentedOut>false</commentedOut>
  <formulaList>...</formulaList>
  <userVariable .../>
</brick>
```

Общие поля:
- `type` — тип блока (например, `SetVariableBrick`, `ShowToastBlock` и десятки/сотни других типов — блоки движения, звука, внешнего вида, управления, физики, датчиков и т.д.)
- `brickId` — уникальный UUID блока.
- `commentedOut` — блок отключён (закомментирован), но сохранён в проекте.
- `formulaList` — список формул (выражений), связанных с параметрами блока.
- Дополнительные специфичные для типа блока поля (например, `userVariable` для блоков работы с переменными).

#### `<formula>` — выражения/формулы

Формулы задают вычисляемые значения параметров блоков (числа, строки, логические условия) в виде дерева разбора:

```xml
<formula category="VARIABLE">
  <leftChild>
    <leftChild>
      <leftChild>
        <type>SENSOR</type>
        <value>DATE_YEAR</value>
      </leftChild>
      <type>FUNCTION</type>
      <value>SIN</value>
    </leftChild>
    <rightChild>
      <type>USER_VARIABLE</type>
      <value>имя_переменной</value>
    </rightChild>
    <type>OPERATOR</type>
    <value>PLUS</value>
  </leftChild>
  <rightChild>
    <type>SENSOR</type>
    <value>OBJECT_WIDTH</value>
  </rightChild>
  <type>OPERATOR</type>
  <value>LOGICAL_OR</value>
</formula>
```

- Это **бинарное дерево выражений**: каждый узел — `leftChild`/`rightChild` + свой `type`/`value`, либо лист.
- `category` — атрибут `<formula>`, обозначающий назначение (в каком контексте используется формула, например `VARIABLE`, `TOAST` и т.д.)
- Типы узлов (`<type>`):
  - `OPERATOR` — арифметический/логический оператор (`PLUS`, `MINUS`, `LOGICAL_OR`, `LOGICAL_AND` и т.д.), у него есть `leftChild` и `rightChild`.
  - `FUNCTION` — встроенная функция (`SIN`, `COS`, `SQRT` и т.д.), обычно с одним `leftChild`-аргументом.
  - `SENSOR` — значение датчика/системной переменной (`DATE_YEAR`, `OBJECT_WIDTH`, координаты, время и т.п.) — лист дерева.
  - `USER_VARIABLE` — ссылка на пользовательскую переменную по имени — лист дерева.
  - `STRING`/`NUMBER` (и подобные) — литеральные константы — лист дерева.
- `additionalChildren` — резерв для функций с переменным числом аргументов (в примере не используется).

#### `<userVariable>` внутри блока

```xml
<userVariable type="UserVariable" serialization="custom">
  <userVariable>
    <default>
      <initialIndex>0</initialIndex>
      <deviceValueKey>UUID</deviceValueKey>
      <name>имя_переменной</name>
    </default>
  </userVariable>
</userVariable>
```

Описывает переменную, к которой обращается блок: её имя, начальное значение/индекс и уникальный ключ хранения на устройстве.

### 3.5. `<programVariableList>`

```xml
<programVariableList>
  <userVariable reference="../../scenes/scene/objectList/object/scriptList/script/brickList/brick/userVariable"/>
</programVariableList>
```

Глобальный (проектный) список переменных. Вместо дублирования данных используется **XML-ссылка (`reference`)** — относительный XPath-подобный путь на первое полное определение той же переменной внутри дерева `<scenes>`. Это механизм сериализации Java/Kotlin XStream (характерно для семейства Catrobat), где повторяющиеся объекты заменяются ссылками на первое вхождение.

### 3.6. `<programListOfLists/>`

Глобальный список программных списков (аналог массивов) — по структуре аналогичен `<programVariableList>`, но для списков.

### 3.7. `<programMultiplayerVariableList/>`

Переменные, синхронизируемые в мультиплеерном/сетевом режиме (специфика NewCatroid как форка с расширенным функционалом).

### 3.8. `<disableScientificNotation>`

Булев флаг: отключать ли научную нотацию при отображении чисел в проекте.

---

## 4. Связь XML и файловой системы архива

| Ссылка в `code.xml` | Где искать файл в архиве |
|---|---|
| `scene/name` | Имя папки сцены в корне архива |
| `look/fileName` (в объекте сцены `S`) | `<S>/images/<fileName>` |
| `sound/fileName` (в объекте сцены `S`) | `<S>/sounds/<fileName>` |
| Произвольные пользовательские данные | `files/` (структура не регламентирована) |

---

## 5. Практические рекомендации для нейросети при разборе `.newtrobat`

1. **Распаковать архив** как ZIP (стандартными библиотеками, например `zipfile` в Python).
2. **Прочитать `code.xml`** через XML-парсер (учитывать UTF-8 и возможные пустые теги).
3. **Разрешить ссылки (`reference="..."`)** в `programVariableList`/`programListOfLists` — при необходимости полного описания переменной нужно перейти по указанному относительному пути внутри того же документа.
4. **Сопоставить ресурсы**: для каждого `look`/`sound` найти реальный файл по пути `<Имя сцены>/images|sounds/<fileName>`.
5. **Не считать `files/` частью логики программы** — это произвольное хранилище, а не часть модели данных Catrobat-программы.
6. **Учитывать множественность сцен**: перебирать все `<scene>` в `<scenes>`, для каждой — свою папку ресурсов.
7. **Дерево формул** обрабатывать рекурсивно (leftChild/rightChild), останавливаясь на листовых типах (`SENSOR`, `USER_VARIABLE`, `STRING`, `NUMBER` и т.п.).
8. Формат является **расширяемым**: NewCatroid — активно развиваемый форк Catrobat/Pocket Code с добавлением новых типов блоков (3D, физика, ИИ для объектов, партиклы и др.), поэтому список `type` для `<brick>`/`<formula>`/`<script>` не является исчерпывающим и должен обрабатываться по возможности обобщённо (unknown-типы — пропускать/логировать, а не считать ошибкой).

---

## 6. Каталог полей и типов блоков (`Brick.java`)

Ниже — справочник по внутренним константам движка Catrobat/NewCatroid (файл `Brick.java`, интерфейс `Brick`). Это **не типы самих блоков** (`brick type="..."`), а типы **полей формул** внутри блока (`BrickField`) — то есть допустимые значения атрибута/тега, к которому привязывается `<formula>` в `<formulaList>` блока. Раздел будет дополняться, так как пользователь предоставляет список поэтапно.

### 6.1. `BrickField` — поля формул блока

`BrickField` реализует маркерный интерфейс `FormulaField` и перечисляет **все возможные "слоты"**, к которым разные типы блоков могут привязать формулу (выражение). У конкретного блока используется только подмножество полей, релевантное его типу (например, `MoveNStepsBrick` использует `STEPS`, `PlaySoundBrick` использует `VOLUME` и т.д.).

Поля сгруппированы тематически (группировка сделана по смыслу имён, не по официальной классификации в коде):

**Визуальные эффекты (внешний вид объекта)**
`COLOR`, `COLOR_CHANGE`, `BRIGHTNESS`, `BRIGHTNESS_CHANGE`, `TRANSPARENCY`, `TRANSPARENCY_CHANGE`, `SIZE`, `SIZE_CHANGE`, `ROTATION`, `ROTATION_STYLE`, `Z_POSITION`

**Позиция и движение**
`X_POSITION`, `Y_POSITION`, `X_POSITION_CHANGE`, `Y_POSITION_CHANGE`, `X_DESTINATION`, `Y_DESTINATION`, `STEPS`, `DEGREES`, `DEGREES_BY`, `TURN_RIGHT_DEGREES`, `TURN_LEFT_DEGREES`, `DURATION_IN_SECONDS`, `POSX`, `POSY`, `POS_X`, `POS_Y`, `POS_Z`, `X`, `Y`, `Z`, `X_SCALE`, `Y_SCALE`

**Звук**
`VOLUME`, `VOLUME_CHANGE`, `TEMPO`, `TEMPO_CHANGE`, `BEATS_TO_PAUSE`, `NOTE_TO_PLAY`, `BEATS_TO_PLAY_NOTE`, `PLAY_DRUM`, `PLAY_SOUND_AT`, `SOUND_NAME`, `PITCH`

**Управление/логика**
`IF_CONDITION`, `TIMES_TO_REPEAT`, `FOR_LOOP_FROM`, `FOR_LOOP_TO`, `REPEAT_UNTIL_CONDITION`, `USER_BRICK`, `USER_DEFINED`, `REPORT_BRICK`, `TEST_FORMULA`

**Переменные и списки**
`VARIABLE`, `VARIABLE_CHANGE`, `VARNAME`, `VARIABLE_NAME`, `VALUE`, `LIST_ADD_ITEM`, `LIST_DELETE_ITEM`, `INSERT_ITEM_INTO_USERLIST_VALUE`, `INSERT_ITEM_INTO_USERLIST_INDEX`, `REPLACE_ITEM_IN_USERLIST_VALUE`, `REPLACE_ITEM_IN_USERLIST_INDEX`, `STORE_CSV_INTO_USERLIST_COLUMN`, `STORE_CSV_INTO_USERLIST_CSV`

**Взаимодействие с пользователем / UI**
`TOAST`, `HEADER`, `BODY`, `TEXT`, `SHOWTEXT`, `QUESTION`, `ASK_QUESTION`, `ASK_SPEECH_QUESTION`, `SPEAK`, `NOTE`, `HINT_TEXT`, `HINT_COLOR`, `TEXTSIZE`, `TEXTCOLOR`, `BGCOLOR`, `PASSWORD`, `MAX_LEN`, `CORNER`, `TYPE`, `ALIGNMENT`, `CONTROLS`, `LOOPED`, `TITLE`, `MESSAGE`, `OK`, `CANEL` *(так в исходнике, опечатка вместо CANCEL)*, `DEFAULT`, `INPUT_TEXT`, `HIDE_STATUS_BAR`, `TEXT_1`…`TEXT_10`

**Сеть / веб**
`URL`, `OPEN_URL`, `WEB_REQUEST`, `IP`, `PORT`, `FILE_URL`, `HTML`, `KEY`, `REGEX`, `TIME`

**Файлы и данные**
`FILE`, `FILE_NAME`, `FILENAME`, `WRITE_FILENAME`, `READ_FILENAME`, `TABLE_NAME`, `PROJECT_NAME`, `PROJECT_FILE_NAME`, `CACHE_NAME`, `DATA`, `CODE`

**Firebase**
`FIREBASE_ID`, `FIREBASE_KEY`, `FIREBASE_VALUE`

**Look/фон/спрайт (ресурсы)**
`LOOK_REQUEST`, `LOOK_NEW`, `LOOK_COPY`, `BACKGROUND_REQUEST`, `LOOK_INDEX`, `BACKGROUND_INDEX`, `BACKGROUND_WAIT_INDEX`, `NAME`, `SCENE_ID`, `SPRITE`, `SPRITE_A`, `SPRITE_B`, `CLONE_NAME`, `INSTANCE_NAME`, `OBJECT_NAME`, `OBJECT_ID`

**Геометрия / размеры / позиционирование UI**
`WIDTH`, `HEIGHT`, `SIZE_X`, `SIZE_Y`, `HORIZONTAL_FLEXIBILITY`, `VERTICAL_FLEXIBILITY`, `BORDERS`

**Физика (2D)**
`PHYSICS_BOUNCE_FACTOR`, `PHYSICS_FRICTION`, `PHYSICS_GRAVITY_X`, `PHYSICS_GRAVITY_Y`, `PHYSICS_MASS`, `PHYSICS_VELOCITY_X`, `PHYSICS_VELOCITY_Y`, `PHYSICS_TURN_LEFT_SPEED`, `PHYSICS_TURN_RIGHT_SPEED`

**Шарниры/суставы (Joints, физика)**
`JOINT_ID`, `JOINT_NAME`, `JOINT_A_ID`, `JOINT_B_ID`, `JOINT_DAMPING`, `JOINT_FREQUENCY`, `JOINT_LENGTH`, `CONSTRAINT_ID`, `MOTOR_TARGET`, `MOTOR_MAX_FORCE`, `AXIS_X`, `AXIS_Y`, `AXIS_A_X`, `AXIS_A_Y`, `AXIS_A_Z`, `AXIS_B_X`, `AXIS_B_Y`, `AXIS_B_Z`, `GROUND_ANCHOR_A_X`, `GROUND_ANCHOR_A_Y`, `GROUND_ANCHOR_B_X`, `GROUND_ANCHOR_B_Y`, `RATIO`, `FORCE_X`, `FORCE_Y`, `IMPULSE_X`, `IMPULSE_Y`, `TORQUE`, `ANGULAR_IMPULSE`, `LINEAR_DAMPING`, `ANGULAR_DAMPING`, `PIVOT_A_X`, `PIVOT_A_Y`, `PIVOT_A_Z`, `PIVOT_B_X`, `PIVOT_B_Y`, `PIVOT_B_Z`, `CHILD_OBJECT`, `PARENT_OBJECT`, `OBJECT_A`, `OBJECT_B`

**Raycast / сенсоры-лучи (расширение NewCatroid)**
`RAY_ID`, `X_START`, `Y_START`, `X_END`, `Y_END`, `DISTANCE`

**3D-объекты и материалы (расширение NewCatroid)**
`THREED_OBJECT_ID`, `THREED_ENABLED`, `THREED_VERTEX_SHADER_CODE`, `THREED_FRAGMENT_SHADER_CODE`, `THREED_UNIFORM_NAME`, `VERTEX`, `FRAGMENT`, `MODEL`, `MASK`, `MATERIAL_R`, `MATERIAL_G`, `MATERIAL_B`, `MATERIAL_A`, `MATERIAL_METALLIC`, `MATERIAL_ROUGHNESS`, `MATERIAL_TEXTURE_COLOR`, `MATERIAL_TEXTURE_NORMAL`, `MATERIAL_TEXTURE_MR`, `GL_VIEW_NAME`, `VALUE_X`, `VALUE_Y`, `VALUE_Z`, `X_1`, `Y_1`, `Z_1`

**Партиклы (система частиц, расширение NewCatroid)**
`PARTICLE_ID`, `PARTICLE_LOOPING`, `PARTICLE_DURATION`, `PARTICLE_LIFETIME`, `PARTICLE_SPEED`, `PARTICLE_SIZE`, `PARTICLE_GRAVITY`, `PARTICLE_MAX_COUNT`, `PARTICLE_RATE`, `PARTICLE_ANGLE`, `PARTICLE_RADIUS`, `PARTICLE_START_COLOR`, `PARTICLE_END_COLOR`, `PARTICLE_END_SIZE`, `PARTICLE_TEXTURE`, `PARTICLE_ADDITIVE`, `PARTICLE_ROTATION`, `PARTICLE_ROTATION_SPEED`, `PARTICLE_POS_X`, `PARTICLE_POS_Y`, `PARTICLE_POS_Z`, `PARTICLE_ROT_PITCH`, `PARTICLE_ROT_YAW`, `PARTICLE_ROT_ROLL`, `EMISSION_RATE`

**Камера / освещение / окружение (3D, расширение NewCatroid)**
`FOV`, `INTENSITY`, `RANGE`, `YAW`, `ROLL`, `SENSITIVITY`, `SHADOW_RESOLUTION`, `SHADOW_SIZE`, `MAX_LIGHTS`, `AVOID_OBSTACLES`, `STEP_HEIGHT`, `TARGET`, `SPEED`, `MODE`, `ENABLED`, `DURATION`, `ZOOM`

**Виртуальная машина / эмуляция (расширение NewCatroid — упоминалось в README как термукс/qemu-интеграция)**
`VM_DISK_SIZE`, `VM_DISK_NAME`, `VM_HDA`, `VM_CDROM`, `VM_CPU`, `VM_MEMORY`, `VM_KEY_DOWN`, `VM_NAME`, `VM_ARGUMENTS`, `VIEW_ID`

**Вышивальные машины (Embroidery, наследие Catrobat)**
`EMBROIDERY_LENGTH`, `ZIGZAG_EMBROIDERY_LENGTH`, `ZIGZAG_EMBROIDERY_WIDTH`, `THREAD_COLOR`

**Тестирование/отладка**
`ASSERT_EQUALS_EXPECTED`, `ASSERT_EQUALS_ACTUAL`, `ASSERT_LOOP_ACTUAL`

**LEGO NXT / EV3 (роботы)**
`LEGO_NXT_SPEED`, `LEGO_NXT_DEGREES`, `LEGO_NXT_FREQUENCY`, `LEGO_NXT_DURATION_IN_SECONDS`, `LEGO_EV3_FREQUENCY`, `LEGO_EV3_DURATION_IN_SECONDS`, `LEGO_EV3_VOLUME`, `LEGO_EV3_SPEED`, `LEGO_EV3_POWER`, `LEGO_EV3_PERIOD_IN_SECONDS`, `LEGO_EV3_DEGREES`

**Parrot Drone / Jumping Sumo**
`DRONE_TIME_TO_FLY_IN_SECONDS`, `DRONE_POWER_IN_PERCENT`, `DRONE_ALTITUDE_LIMIT`, `DRONE_VERTICAL_SPEED_MAX`, `DRONE_ROTATION_MAX`, `DRONE_TILT_ANGLE`, `JUMPING_SUMO_SPEED`, `JUMPING_SUMO_TIME_TO_DRIVE_IN_SECONDS`, `JUMPING_SUMO_VOLUME`, `JUMPING_SUMO_ROTATE`

**Phiro (робот)**
`PHIRO_SPEED`, `PHIRO_DURATION_IN_SECONDS`, `PHIRO_LIGHT_RED`, `PHIRO_LIGHT_GREEN`, `PHIRO_LIGHT_BLUE`

**Arduino / Raspberry Pi**
`ARDUINO_ANALOG_PIN_VALUE`, `ARDUINO_ANALOG_PIN_NUMBER`, `ARDUINO_DIGITAL_PIN_VALUE`, `ARDUINO_DIGITAL_PIN_NUMBER`, `RASPI_DIGITAL_PIN_VALUE`, `RASPI_DIGITAL_PIN_NUMBER`, `RASPI_PWM_PERCENTAGE`, `RASPI_PWM_FREQUENCY`

**NFC**
`NFC_NDEF_MESSAGE`

**Прочее / общего назначения**
`STRING`, `STRING_VALUE`, `RED`, `GREEN`, `BLUE`, `ALPHA`, `PEN_SIZE`, `PEN_COLOR_RED`, `PEN_COLOR_GREEN`, `PEN_COLOR_BLUE`, `VIBRATE_DURATION_IN_SECONDS`, `VIBRATE_DURATION`, `TIME_TO_WAIT_IN_SECONDS`, `INTERVAL`, `SCRIPT`, `FLOAT_ARRAY`
Также присутствуют универсальные слоты-заглушки без строгой семантики: `VALUE_1`…`VALUE_17` (кроме `VALUE_8`, если он не встречался — фактически охвачены `VALUE`, `VALUE_1`–`VALUE_17`), `FORMULA_1`…`FORMULA_7`, `CUSTOM_PARAM_1`…`CUSTOM_PARAM_10` — используются для параметризуемых/пользовательских блоков и блоков расширений, где нет отдельного именованного поля.

> **Важно для парсинга:** значение `<formula category="X">` в `code.xml`, где `X` — одно из этих имён (например, `VARIABLE`, `TOAST`, `STEPS`), — это и есть конкретный `BrickField`, к которому относится формула. Зная тип `brick` и присвоенную ему категорию формулы, можно понять семантику параметра без документации по каждому блоку отдельно.

Также в `BrickField` определён вспомогательный список:
```java
EXPECTS_STRING_VALUE = {VARIABLE, NOTE, SPEAK, STRING, ASK_QUESTION,
    NFC_NDEF_MESSAGE, ASK_SPEECH_QUESTION, LIST_ADD_ITEM,
    INSERT_ITEM_INTO_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_VALUE}
```
Поля из этого списка ожидают **строковое** значение результата формулы (а не число/булево).

### 6.2. `BrickData` — данные блоков для списков

```java
enum BrickData {
    ASSERT_LISTS_EXPECTED, ASSERT_LISTS_ACTUAL,
    FOR_ITEM_IN_USERLIST_LIST, FOR_ITEM_IN_USERLIST_VARIABLE;
}
```
Отдельный (от `BrickField`) маркер полей, которые оперируют не формулой, а **пользовательским списком** (`UserList`) целиком — используется, например, в блоке цикла "для каждого элемента списка" (`FOR_ITEM_IN_USERLIST_LIST`/`FOR_ITEM_IN_USERLIST_VARIABLE`) и в блоках сравнения списков при тестировании (`ASSERT_LISTS_EXPECTED/ACTUAL`). Подмножество `EXPECTS_USERLIST` = `{ASSERT_LISTS_EXPECTED, ASSERT_LISTS_ACTUAL, FOR_ITEM_IN_USERLIST_LIST}` помечает поля, обязательно ссылающиеся на список, а не на переменную.

### 6.3. `Resources` — декларируемые ресурсы/разрешения блока

Каждый блок через `addRequiredResources(ResourcesSet)` может декларировать, какие аппаратные/программные ресурсы устройства ему нужны для выполнения (аналог permissions). Это целочисленные константы (не строки XML), используемые внутри приложения-исполнителя, но полезные для понимания семантики блоков:

| Значение | Ресурс |
|---|---|
| 1 | `TEXT_TO_SPEECH` — синтез речи |
| 2 | `BLUETOOTH_LEGO_NXT` |
| 3 | `PHYSICS` — физический движок |
| 4 | `FACE_DETECTION` — распознавание лиц |
| 5 | `TEXT_DETECTION` — распознавание текста |
| 6 | `BLUETOOTH_SENSORS_ARDUINO` |
| 7 | `SOCKET_RASPI` |
| 8 | `CAMERA_FLASH` |
| 9 | `VIBRATION` |
| 10 | `BLUETOOTH_PHIRO` |
| 11 | `CAMERA_BACK` |
| 12 | `CAMERA_FRONT` |
| 13 | `SENSOR_ACCELERATION` |
| 14 | `SENSOR_INCLINATION` |
| 15 | `SENSOR_COMPASS` |
| 16 | `NFC_ADAPTER` |
| 17 | `VIDEO` |
| 18 | `SENSOR_GPS` |
| 19 | `COLLISION` |
| 20 | `BLUETOOTH_LEGO_EV3` |
| 21 | `NETWORK_CONNECTION` |
| 22 | `CAST_REQUIRED` |
| 23 | `SPEECH_RECOGNITION` |
| 24 | `MICROPHONE` |
| 25 | `STORAGE_READ` |
| 26 | `STORAGE_WRITE` |
| 27 | `POSE_DETECTION` |
| 28 | `OBJECT_DETECTION` |
| 29 | `IMAGE` |
| 30 | `AUDIO` |
| 31 | `DOCUMENT` |
| 32 | `OTHER` |

Это влияет на то, какие разрешения/компоненты нужно эмулировать или на что обращать внимание при анализе безопасности/совместимости проекта.

### 6.4. Прочее из `Brick.java`, важное для интерпретации `code.xml`

- Каждый блок имеет уникальный `UUID` (`getBrickID()`) — соответствует тегу `<brickId>` в XML.
- Блоки могут быть **составными** (`consistsOfMultipleParts()`, `getAllParts()`) — то есть один логический блок в XML может разворачиваться в несколько связанных `<brick>` (типично для конструкций типа "если... иначе..." — начало/конец блока представлены отдельными `<brick>` с одинаковой логической группой).
- Блоки образуют дерево через `getParent()`/`setParent()` и `getDragAndDropTargetList()` — то есть вложенные блоки (внутри циклов/условий) физически являются частью `brickList` родителя, но с указанием иерархии.
- `isCommentedOut()`/`setCommentedOut()` — соответствует тегу `<commentedOut>` в XML: блок присутствует в файле, но не выполняется.
- `hasHelpPage()`/`getHelpUrl(category)` — у части блоков есть встроенная справка (не хранится в `code.xml`, генерируется по типу блока).
- `isPhantom()` — служебный флаг "блока-призрака" (используется для промежуточных/вспомогательных блоков, не показываемых напрямую пользователю).

> Раздел является **накопительным**: при получении от пользователя дополнительных списков (типы `brick`, типы `script`, операторы формул `OPERATOR`/`FUNCTION`/`SENSOR` и т.п. из других исходников проекта) документ будет дополнен соответствующими подразделами 6.5, 6.6 и далее.

### 6.5. Каталог конкретных типов блоков (`Brick`, из `BrickInfo.java`)

`BrickInfo.java` — локализованный справочник NewCatroid: словарь `Class<? extends Brick> → строка описания` (отдельно для ru/en/pt/zh). Это даёт "человеческую" расшифровку значения `brick type="..."` в `code.xml`: имя класса совпадает с значением атрибута `type` за вычетом суффикса `.class` (например, `add(MoveNStepsBrick.class, ...)` → в XML это `<brick type="MoveNStepsBrick">`).

Ниже — полный перечень встретившихся типов (393 уникальных, версия NewCatroid 2.2.0+), сгруппированный тематически. Каждое имя — валидное значение `brick/@type`. Точные формулировки описаний на русском содержатся в исходнике `BrickInfo.java` (`initRussianDescriptions()`), здесь при необходимости даны только пояснения к неочевидным группам.

**Управление потоком и скриптами**
`ForeverBrick`, `RepeatBrick`, `AsyncRepeatBrick`, `IntervalRepeatBrick`, `RepeatUntilBrick`, `WaitUntilBrick`, `WaitBrick`, `WaitTillIdleBrick`, `InstantBrick`, `IfThenLogicBeginBrick`, `IfLogicElseBrick`, `IfThenLogicEndBrick`, `IfOnEdgeBounceBrick`, `ForItemInUserListBrick`, `ForVariableFromToBrick`, `RunAsSpriteBrick`, `SpawnThreadBrick`, `WaitThreadBrick`, `StopThreadBrick`, `TryCatchFinallyBrick`, `StopScriptBrick`, `NoteBrick`

**События (`When...`) и сообщения**
`WhenStartedBrick`, `WhenBrick`, `WhenTouchDownBrick`, `WhenConditionBrick`, `WhenBackgroundChangesBrick`, `WhenClonedBrick`, `WhenClonedWithNameBrick`, `WhenBounceOffBrick`, `WhenBeforeUpdateBrick`, `WhenAfterUpdateBrick`, `WhenBackPressedBrick`, `WhenProjectExitsBrick`, `WhenSpriteReleasedBrick`, `WhenFingerMovedOverSpriteBrick`, `WhenFingerMovedOnScreenBrick`, `WhenWindowResizedBrick`, `WhenAppMinimizedBrick`, `WhenAppRestoredBrick`, `WhenNotificationActionTriggeredBrick`, `WhenNotificationClickedBrick`, `WhenMqttMessageBrick`, `BroadcastBrick`, `BroadcastWaitBrick`, `BroadcastReceiverBrick`

**Сцены и жизненный цикл проекта**
`SceneStartBrick`, `SceneIdBrick`, `SceneTransitionBrick`, `ClearSceneBrick`, `SetSaveScenesBrick`, `SetStopSoundsBrick`, `LoadSceneBrick`, `LoadSceneAdditiveBrick`, `ReturnToPreviousProjectBrick`, `LaunchProjectBrick`, `FinishStageBrick`

**Клоны**
`CloneBrick`, `CloneAndNameBrick`, `DeleteThisCloneBrick`

**Движение и позиционирование (2D)**
`MoveNStepsBrick`, `GoNStepsBackBrick`, `GoToBrick`, `GlideToBrick`, `PlaceAtBrick`, `SetXBrick`, `SetYBrick`, `ChangeXByNBrick`, `ChangeYByNBrick`, `TurnRightBrick`, `TurnLeftBrick`, `PointInDirectionBrick`, `PointToBrick`, `SetRotationStyleBrick`, `ComeToFrontBrick`

**Физика (2D, шарниры/joints, raycast)**
`ApplyForceBrick`, `ApplyImpulseBrick`, `ApplyTorqueBrick`, `ApplyAngularImpulseBrick`, `Apply3dTorqueBrick`, `SetDampingBrick`, `SetVelocityBrick`, `TurnRightSpeedBrick`, `TurnLeftSpeedBrick`, `SetGravityBrick`, `SetMassBrick`, `SetRestitutionBrick`, `SetFrictionBrick`, `SetPhysicsObjectTypeBrick`, `SetPhysicsStateBrick`, `SetHitboxBrick`, `SetCCDBrick`, `PerformRayCastBrick`, `AttachRaySensorBrick`, `BakeByPrefixBrick`, `AddHingeBrick`, `SetHingeMotorBrick`, `CreateRevoluteJointBrick`, `CreatePulleyJointBrick`, `CreateGearJointBrick`, `CreateDistanceJointBrick`, `CreateWeldJointBrick`, `CreatePrismaticJointBrick`, `CreatePointJointBrick`, `DestroyJointBrick`, `RemoveJointBrick`

**Внешний вид / образы (looks)**
`SetLookBrick`, `SetLookByIndexBrick`, `NextLookBrick`, `PreviousLookBrick`, `SetSizeToBrick`, `ChangeSizeByNBrick`, `SetWidthBrick`, `SetHeightBrick`, `ChangeWidthBrick`, `ChangeHeightBrick`, `SetTransparencyBrick`, `ChangeTransparencyByNBrick`, `SetBrightnessBrick`, `ChangeBrightnessByNBrick`, `SetColorBrick`, `ChangeColorByNBrick`, `ClearGraphicEffectBrick`, `EasePropertyBrick`, `HideBrick`, `ShowBrick`, `CopyLookBrick`, `DeleteLookBrick`, `CutLookBrick`, `EditLookBrick`, `PaintNewLookBrick`, `LookRequestBrick`, `LookFileBrick`, `SaveLookBrick`, `SaveLookFilesBrick`, `LookToTableBrick`, `LookFromTableBrick`, `ScreenShotBrick`, `PhotoBrick`, `ResizeImgBrick`, `GrayscaleImgBrick`, `NormalizeImgBrick`, `ApplyShaderToImageBrick`, `SetCornerOffsetsBrick`, `PlayGifBrick`, `StopGifBrick`, `PlaySpritesheetBrick`, `StopSpritesheetBrick`

**Фон**
`SetBackgroundBrick`, `SetBackgroundByIndexBrick`, `SetBackgroundAndWaitBrick`, `SetBackgroundByIndexAndWaitBrick`

**Частицы**
`CreateParticlesBrick`, `DeleteParticlesBrick`, `FadeParticleEffectBrick`, `SetParticleColorBrick`, `ConfigureParticlesBrick`

**Камера**
`CameraBrick`, `ChooseCameraBrick`, `FlashBrick`, `SetCameraFocusPointBrick`, `SetCameraPosition2Brick`, `SetCameraRotation2Brick`, `SetCameraZoomBrick`, `SetThirdPersonCameraBrick`, `SetFreeCameraBrick`, `PinToCameraBrick`, `UnpinFromCameraBrick`, `AttachToCameraBrick`, `DetachFromCameraBrick`, `RotateCameraByBrick`, `CameraTouchControlBrick`, `CameraSettingsBrick`, `CameraTrackingBrick`

**Звук**
`PlaySoundBrick`, `PlaySoundAndWaitBrick`, `PlaySoundAtBrick`, `SoundFileBrick`, `SoundFilesBrick`, `PrepareSoundBrick`, `PrepareSoundBrick2`, `PlayPreparedSoundBrick`, `StopSoundBrick`, `StopSoundBrick2`, `StopAllSoundsBrick`, `SetVolumeToBrick`, `SetSoundVolumeBrick`, `ChangeVolumeByNBrick`, `StartListeningBrick`, `StartRecordingBrick`, `StopRecordingBrick`, `PrepareMusicAs3DSoundBrick`, `PlaySoundAtPositionBrick`, `Set3DSoundMaxDistanceBrick`, `Set3DSoundPositionBrick`, `SetGlobalSoundVolumeBrick`

**Речь / TTS**
`SpeakBrick`, `SpeakAndWaitBrick`, `AskSpeechBrick`

**Диалоги, ввод, интерфейс сообщений**
`AskBrick`, `BigAskBrick`, `CreateDialogBrick`, `SetPositiveBrick`, `SetNeutralBrick`, `SetNegativeBrick`, `AddEditBrick`, `AddRadioBrick`, `SetCallbackBrick`, `ShowDialogBrick`, `ShowToastBlock`, `CopyTextBrick`

**Файлы, переменные на диске, архивы, текст**
`ChooseFileBrick`, `DeleteFilesBrick`, `OpenFileBrick`, `FileUrlBrick`, `FilesUrlBrick`, `MoveFilesBrick`, `MoveDownloadsBrick`, `CopyProjectFileBrick`, `ExportProjectFileBrick`, `SaveToInternalStorageBrick`, `LoadFromInternalStorageBrick`, `WriteVariableOnDeviceBrick`, `ReadVariableFromDeviceBrick`, `WriteVariableToFileBrick`, `ReadVariableFromFileBrick`, `WriteToFilesBrick`, `ReadFromFilesBrick`, `ZipBrick`, `ZipProjectFilesBrick`, `UnzipBrick`, `UnzipProjectFilesBrick`, `GetZipFileNamesBrick`, `StoreCSVIntoUserListBrick`, `SplitBrick`, `RegexBrick`, `Base64ToFileBrick`

**Сеть, HTTP, серверы, Firebase, MQTT-мультиплеер**
`WebRequestBrick`, `PostWebRequestBrick`, `HttpCreateBrick`, `HttpConfigBrick`, `HttpBodyBrick`, `HttpAttachFileBrick`, `HttpSendBrick`, `HttpSaveFileBrick`, `StartServerBrick`, `ConnectServerBrick`, `ListenServerBrick`, `SendServerBrick`, `StopServerBrick`, `WriteBaseBrick`, `ReadBaseBrick`, `DeleteBaseBrick`, `UploadFileBrick`, `ShareBrick`, `MqttConnectBrick`, `MqttJoinRoomBrick`, `MqttPublishBrick`, `MqttDisconnectBrick`

**ИИ / нейросети**
`SetGeminiKeyBrick`, `AskGeminiBrick`, `AskGemini2Brick`, `AskGPTBrick`, `CreateFloatBrick`, `PutFloatBrick`, `DeleteFloatBrick`, `TableToFloatBrick`, `LoadNNBrick`, `PredictNNBrick`, `UnloadNNBrick`, `SetAIBrick` (объектный ИИ обхода препятствий, не связан с LLM-блоками выше)

**Встраиваемые языки и выполнение кода**
`RunJSBrick`, `RunLuaBrick`, `LunoScriptBrick`, `ClearPythonEnvironmentBrick`, `LoadNativeModuleBrick`, `LoadPythonLibraryBrick`, `RunPythonScriptBrick`, `RunShellBrick`, `RunChip8Brick`, `JavaCompileBrick`, `JavaLoadAndRunBrick`, `JavaDownloadDepBrick`

**Виртуальная машина (QEMU/VNC)**
`RunVMBrick`, `RunVm2Brick`, `StopVMBrick`, `CreateDiskBrick`, `VmSetMonitorSizeBrick`, `ToggleDisplayBrick`, `MouseEventBrick`, `VmRelativeMouseMoveBrick`, `KeyEventBrick`, `SendVmInputBrick`, `BindVmOutputBrick`

**3D-объекты, материалы, свет, рендер**
`Create3dObjectBrick`, `CreateCubeBrick`, `CreateSphereBrick`, `Remove3dObjectBrick`, `CloneObjectBrick`, `SetObjectColorBrick`, `SetObjectTextureBrick`, `Set3dScaleBrick`, `SetMaterialBrick`, `SetShaderCodeBrick`, `SetScreenShaderBrick`, `SetObjectShaderBrick`, `SetObjectShaderUniformBrick`, `ConfigureLightBrick`, `ConfigureMaterialBrick`, `PromoteLightBrick`, `SetPointLightBrick`, `SetSpotLightBrick`, `SetDirectionalLightBrick`, `SetMaxPointLightsBrick`, `Replace3DModelBrick`, `Export3dObjectToGlbBrick`, `PlayAnimationBrick`, `EnablePbrRenderBrick`, `SetAnisotropicFilterBrick`, `SetRenderResolutionBrick`, `SetFpsBrick`, `SetShadowQualityBrick`, `SetPostProcessingBrick`, `SetPostProcessingNewBrick`, `RemoveObjectsByPrefixBrick`, `SetActiveBrick`, `SetParentBrick`, `RemoveParentBrick`, `Ease3DPropertyBrick`

**Кадровые буферы (FrameBuffer / рендер в текстуру)**
`CreateBufferBrick`, `SetBufferModeBrick`, `SetBufferAutoUpdateBrick`, `AddToBufferBrick`, `RemoveFromBufferBrick`, `SetBufferOnlyBrick`, `SetBufferCameraBrick`, `SetBufferCamera3DBrick`, `ApplyBufferLookBrick`, `SaveBufferBrick`, `AddTextToBufferBrick`, `SetBufferShaderBrick`, `SetBufferShaderUniformBrick`, `SetMainRenderLoopsBrick`, `SetBufferEffectsBrick`, `SetTextBufferOnlyBrick`, `StartBufferRecordingBrick`, `StopBufferRecordingBrick`, `BufferMaskBrick`

**Нативный UI (View поверх сцены)**
`CreateButtonBrick`, `CreateSwitchBrick`, `CreateImageViewBrick`, `CreateSliderBrick`, `CreateScrollViewBrick`, `CreateTextLabelBrick`, `CreateTextFieldBrick`, `CreateVideoBrick`, `CreateWebFileBrick`, `CreateWebUrlBrick`, `CreateGLViewBrick`, `SetWebBrick`, `EvalWebBrick`, `AttachSOBrick`, `DeleteWebBrick`, `SetNativeParentBrick`, `NativeViewConfigBrick`, `NativeViewAnimateBrick`, `NativeViewListenerBrick`, `NativeViewBindSpriteBrick`, `NativeViewControlBrick`

**Уведомления и фоновый режим**
`ShowNotificationBrick`, `NotificationCreateBrick`, `NotificationShowBrick`, `NotificationAddButtonBrick`, `NotificationCancelBrick`, `WhenNotificationClickedBrick`, `WhenNotificationActionTriggeredBrick`, `EnableBackgroundModeBrick`, `DisableBackgroundModeBrick`

**Перо (Pen, векторная графика на холсте)**
`SetPenPropertyBrick`, `PenDrawLineBrick`, `PenDrawTriangleBrick`, `PenDrawRectBrick`, `PenDrawCircleBrick`, `PenClearColorBrick`, `PenFlushBrick`

**Текст как отдельный слой / примитивы 2D**
`SetTextPropertyBrick`, `SquareBrick`, `DelSquareBrick`

**Переменные, таблицы, вибрация, прочее системное**
`CreateVarBrick`, `CreateTableBrick`, `VibrationBrick`, `OpenAppBrick`, `OrientationBrick`

> Полные, дословные описания на русском/английском/португальском/китайском для каждого из этих типов содержатся в `BrickInfo.java` (методы `initRussianDescriptions()`, `initEnglishDescriptions()`, `initPortugueseDescriptions()`, `initChineseDescriptions()`) в виде `add(ИмяБлока.class, "описание")`. Для получения текста описания конкретного блока при парсинге `code.xml` нужно взять значение `brick/@type` и найти соответствующую запись `add(<type>.class, ...)` в нужной языковой секции.

### 6.6. Новые наблюдения из обновлённого `code.xml` (формулы, списки, ссылки)

Второй предоставленный пример `code.xml` (проект "Отправка мелких медиа") демонстрирует несколько ранее не задокументированных механизмов формата:

**Многоаргументные функции формул (`additionalChildren`)**
Ранее `additionalChildren` встречался пустым. В новом примере он используется для функций с более чем двумя аргументами: узел `<formula>` хранит первые два аргумента как обычно в `leftChild`/`rightChild`, а остальные — как последовательность вложенных `<org.catrobat.catroid.formulaeditor.FormulaElement>` внутри `<additionalChildren>`. Пример — функция `JOIN3` (конкатенация 3 строк):
```xml
<formula category="VARIABLE">
  <additionalChildren>
    <org.catrobat.catroid.formulaeditor.FormulaElement>
      <leftChild><type>USER_VARIABLE</type><value>окак</value></leftChild>
      <type>FUNCTION</type>
      <value>FILE_TO_BASE64</value>
    </org.catrobat.catroid.formulaeditor.FormulaElement>
  </additionalChildren>
  <leftChild><type>USER_VARIABLE</type><value>окак</value></leftChild>
  <rightChild><type>STRING</type><value>;</value></rightChild>
  <type>FUNCTION</type>
  <value>JOIN3</value>
</formula>
```
Здесь `JOIN3(окак, ";", FILE_TO_BASE64(окак))` — то есть третий аргумент сам является вложенной формулой произвольной сложности, а не просто литералом.

**Новые обнаруженные функции формул (`FUNCTION`)**
- `FILE_TO_BASE64` — кодирует файл (путь берётся из значения аргумента) в строку Base64.
- `JOIN3` — конкатенация трёх строковых значений (в отличие от базового `JOIN`, объединяющего два).
- `LIST_ITEM` — получает элемент списка по индексу: первый аргумент (`leftChild`) — индекс (начиная с 1), второй (`rightChild`) — ссылка на список через узел `USER_LIST`.

Это подтверждает раздел 3.4: набор функций/операторов формул открыт и расширяется независимо от `BrickField`; при парсинге незнакомый `<value>` внутри `<type>FUNCTION</type>` следует трактовать как потенциально валидную, но недокументированную встроенную функцию, а не как ошибку.

**Тип узла формулы `USER_LIST`**
Помимо `USER_VARIABLE`, формулы могут ссылаться на пользовательский список по имени через узел:
```xml
<leftChild>
  <type>USER_LIST</type>
  <value>Название + строка</value>
</leftChild>
```

**Структура объявления списка (`<userList>`)**
Блоки, создающие список (например, `SplitBrick`), содержат тег `<userList>` — аналог `<userVariable>`, но для списков, без вложенной обёртки `default`:
```xml
<userList>
  <deviceListKey>UUID</deviceListKey>
  <initialIndex>0</initialIndex>
  <name>Название списка</name>
</userList>
```
Глобальный реестр списков хранится в `<programListOfLists>` тем же паттерном ссылок, что и переменные (см. 3.5):
```xml
<programListOfLists>
  <userList reference="../../scenes/scene/objectList/object[2]/scriptList/script/brickList/brick/userList"/>
</programListOfLists>
```

**Индексированные XPath-ссылки при повторяющихся тегах**
В разделе 3.5 было показано простое `reference="../../scenes/scene/objectList/object/scriptList/script/brickList/brick/userVariable"`. Когда в пределах одного родителя несколько одноимённых сиблингов (например, несколько `<brick>` с `userVariable`, или несколько `<object>` в сцене), сериализатор использует **1-based индекс в квадратных скобках** для однозначного указания нужного вхождения: `object[2]`, `brick[2]`, `brick[3]` и т.д. Отсутствие индекса означает первое (или единственное) вхождение. Это стандартное поведение XStream-сериализации (используемой Catrobat/NewCatroid) и должно учитываться при разрешении ссылок программным парсером.

**Дополнительные атрибуты конкретных блоков**
Помимо `formulaList`/`userVariable`/`userList`, отдельные типы блоков имеют собственные простые теги-параметры вне формул, например `<fileTypeSelection>4</fileTypeSelection>` у `ChooseFileBrick` (числовой код выбранного типа файла в диалоге выбора). Такие поля специфичны для типа блока и не описываются общей схемой `Brick.java`/`BrickField` — их назначение нужно уточнять по конкретной реализации блока (см. `BrickInfo.java` для смыслового описания блока в целом).

### 6.7. Датчики и свойства объекта (`Sensors.java`)

В `code.xml` это узел формулы `<type>SENSOR</type><value>ИМЯ</value>`. Допустимые значения `value` — константы enum `Sensors`. У каждой константы есть флаг `isObjectSensor`: `true` означает **свойство объекта** (спрайта), а не аппаратный датчик устройства. То есть «свойства» и «датчики» в формулах лежат в одном enum и различаются только этим флагом.

**Свойства объекта (`isObjectSensor = true`)**
`OBJECT_X`, `OBJECT_Y`, `OBJECT_TRANSPARENCY`, `OBJECT_BRIGHTNESS`, `OBJECT_COLOR`, `OBJECT_SIZE`, `OBJECT_WIDTH`, `OBJECT_HEIGHT`, `WIDTH`, `HEIGHT`, `MOTION_DIRECTION`, `LOOK_DIRECTION`, `OBJECT_LAYER`, `OBJECT_DISTANCE_TO`, `OBJECT_NAME`, `COLLIDES_WITH_EDGE`, `COLLIDES_WITH_FINGER`, `OBJECT_X_VELOCITY`, `OBJECT_Y_VELOCITY`, `OBJECT_ANGULAR_VELOCITY`, `OBJECT_LOOK_NUMBER`, `OBJECT_LOOK_WIDTH`, `OBJECT_LOOK_HEIGHT`, `OBJECT_LOOK_NAME`, `OBJECT_NUMBER_OF_LOOKS`, `OBJECT_BACKGROUND_NUMBER`, `OBJECT_BACKGROUND_NAME`, `NFC_TAG_ID`, `NFC_TAG_MESSAGE`

**Датчики устройства и системы (`isObjectSensor = false`)**

| Группа | Значения |
|---|---|
| Акселерометр / ориентация | `X_ACCELERATION`, `Y_ACCELERATION`, `Z_ACCELERATION`, `COMPASS_DIRECTION`, `X_INCLINATION`, `Y_INCLINATION` |
| Звук | `LOUDNESS`, `MICRO` |
| Геолокация | `LATITUDE`, `LONGITUDE`, `LOCATION_ACCURACY`, `ALTITUDE` |
| Язык | `USER_LANGUAGE`, `SPEECH_RECOGNITION_LANGUAGE` |
| Время и дата | `TIMER`, `DATE_YEAR`, `DATE_MONTH`, `DATE_DAY`, `DATE_WEEKDAY`, `TIME_HOUR`, `TIME_MINUTE`, `TIME_SECOND` |
| Лицо | `FACE_DETECTED`, `FACE_SIZE`, `FACE_X`, `FACE_Y`, `SECOND_FACE_DETECTED`, `SECOND_FACE_SIZE`, `SECOND_FACE_X`, `SECOND_FACE_Y` |
| Поза тела (пары `*_X` / `*_Y`) | голова и шея (`HEAD_TOP`, `NECK`, `NOSE`), глаза (`LEFT/RIGHT_EYE_INNER/CENTER/OUTER`), уши, уголки рта, плечи, локти, запястья, мизинцы, указательные и большие пальцы, бёдра, колени, лодыжки, пятки, `*_FOOT_INDEX` |
| Касания экрана | `LAST_FINGER_INDEX`, `FINGER_X`, `FINGER_Y`, `FINGER_TOUCHED`, `NUMBER_CURRENT_TOUCHES` |
| Мышь и клавиатура | `MOUSE_X`, `MOUSE_Y`, `MOUSE_DELTA_X`, `MOUSE_DELTA_Y`, `MOUSE_SCROLL`, `KEYBOARD_HEIGHT`, `CLIPBOARD_TEXT` |
| Геймпад | `GAMEPAD_A_PRESSED`, `GAMEPAD_B_PRESSED`, `GAMEPAD_UP_PRESSED`, `GAMEPAD_DOWN_PRESSED`, `GAMEPAD_LEFT_PRESSED`, `GAMEPAD_RIGHT_PRESSED` |
| Распознавание текста | `TEXT_FROM_CAMERA`, `TEXT_BLOCKS_NUMBER`, `TEXT_BLOCK_X`, `TEXT_BLOCK_Y`, `TEXT_BLOCK_SIZE`, `TEXT_BLOCK_FROM_CAMERA`, `TEXT_BLOCK_LANGUAGE_FROM_CAMERA` |
| NFC | `NFC_TECH_LIST`, `NFC_MEMORY_SIZE`, `NFC_IS_WRITABLE`, `NFC_TAG_TYPE` |
| Сцена и система | `STAGE_WIDTH`, `STAGE_HEIGHT`, `IP`, `PORT`, `FREQ`, `INTERNET`, `BATTARY` *(так в исходнике, опечатка вместо BATTERY)*, `ARCH`, `FPS` |
| LEGO | `NXT_SENSOR_1`…`NXT_SENSOR_4`, `EV3_SENSOR_1`…`EV3_SENSOR_4` |
| Phiro | `PHIRO_FRONT_LEFT`, `PHIRO_FRONT_RIGHT`, `PHIRO_SIDE_LEFT`, `PHIRO_SIDE_RIGHT`, `PHIRO_BOTTOM_LEFT`, `PHIRO_BOTTOM_RIGHT` |
| Drone | `DRONE_BATTERY_STATUS`, `DRONE_EMERGENCY_STATE`, `DRONE_FLYING`, `DRONE_INITIALIZED`, `DRONE_USB_ACTIVE`, `DRONE_USB_REMAINING_TIME`, `DRONE_CAMERA_READY`, `DRONE_RECORD_READY`, `DRONE_RECORDING`, `DRONE_NUM_FRAMES` |

**Булевы датчики** (набор `Sensors.BOOLEAN`, результат трактуется как истина/ложь): `FACE_DETECTED`, `SECOND_FACE_DETECTED`, `DRONE_FLYING`, `DRONE_INITIALIZED`, `DRONE_USB_ACTIVE`, `DRONE_CAMERA_READY`, `DRONE_RECORDING`, `DRONE_RECORD_READY`, все шесть `GAMEPAD_*_PRESSED`, `FINGER_TOUCHED`, `COLLIDES_WITH_FINGER`, `COLLIDES_WITH_EDGE`, `NFC_IS_WRITABLE`.

### 6.8. Функции формул (`Functions.java`)

В `code.xml` это узел `<type>FUNCTION</type><value>ИМЯ</value>`. Допустимые значения — константы enum `Functions` (около 230). Аргументы лежат в `leftChild`, `rightChild` и далее в `additionalChildren` (см. 6.6).

| Группа | Значения |
|---|---|
| Математика | `SIN`, `COS`, `TAN`, `ARCSIN`, `ARCCOS`, `ARCTAN`, `ARCTAN2`, `LN`, `LOG`, `SQRT`, `EXP`, `POWER`, `ABS`, `PI`, `MOD`, `ROUND`, `ROUNDTO`, `FLOOR`, `CEIL`, `MAX`, `MIN`, `CLAMP`, `RAND`, `TRUE`, `FALSE`, `TO_HEX`, `TO_DEC`, `DISTAN`, `DELTA` |
| Строки | `LENGTH`, `LETTER`, `SUBTEXT`, `UPPER`, `LOWER`, `REVERSE`, `REPLACE`, `REPEAT`, `JOIN`, `JOIN3`, `JOINNUMBER`, `REGEX`, `CONTAINS_STR`, `RANDOM_STR`, `CHAR_TO_UNICODE`, `UNICODE_TO_CHAR`, `UNESCAPE_UTF`, `MD5`, `SHA256`, `IF_THEN_ELSE` |
| Переменные | `VAR`, `VARNAME`, `VARVALUE` |
| Списки (набор `LIST`) | `LIST_ITEM`, `CONTAINS`, `INDEX_OF_ITEM`, `NUMBER_OF_ITEMS`, `FLATTEN`, `CONNECT`, `FIND` |
| Таблицы | `TABLE_X`, `TABLE_Y`, `TABLE_ELEMENT`, `TABLE_JOIN` |
| JSON | `JSON_GET`, `JSON_SET`, `JSON_IS_VALID` |
| Файлы | `FILE`, `READ_FILE`, `FILES_PATH`, `ALL_FILES`, `FILE_SIZE`, `FILE_LAST_MODIFIED`, `FILE_TO_BASE64`, `FILE_MD5`, `FILE_SHA256`, `MEDIA_DURATION`, `IMAGE_WIDTH`, `IMAGE_HEIGHT` |
| Скрипты и массивы | `LUA`, `FLOATARRAY` |
| Нативные View и видео | `VIEW_X`, `VIEW_Y`, `VIEW_WIDTH`, `VIEW_HEIGHT`, `VIDEO_PLAYING`, `VIDEO_TIME` |
| Касания | `MULTI_FINGER_X`, `MULTI_FINGER_Y`, `MULTI_FINGER_TOUCHED`, `INDEX_CURRENT_TOUCH`, `IS_MOUSE_BUTTON_DOWN` |
| Цвет и столкновения | `COLLIDES_WITH_COLOR`, `COLOR_TOUCHES_COLOR`, `COLOR_AT_XY`, `COLOR_EQUALS_COLOR`, `TOUCHES_OBJECT_BY_NAME`, `COLLISION_LIST`, `INTERSECT_LIST`, `OBJECT_TOUCHES_OBJECT`, `OBJECT_INTERSECTS_OBJECT` |
| Распознавание текста | `TEXT_BLOCK_X`, `TEXT_BLOCK_Y`, `TEXT_BLOCK_SIZE`, `TEXT_BLOCK_FROM_CAMERA`, `TEXT_BLOCK_LANGUAGE_FROM_CAMERA` |
| 3D: позиция, поворот, масштаб, скорость | `GET_3D_POSITION_X/Y/Z`, `GET_3D_ROTATION_YAW/PITCH/ROLL`, `GET_3D_SCALE_X/Y/Z`, `GET_3D_VELOCITY_X/Y/Z`, `GET_3D_DISTANCE`, `GET_DIRECTION_X`, `GET_DIRECTION_Y`, `GET_ANGLE` |
| 3D: камера | `GET_CAMERA_POS_X/Y/Z`, `GET_CAMERA_DIR_X/Y/Z`, `GET_CAMERA_ROTATION_YAW/PITCH/ROLL` |
| 3D и 2D: лучи | `GET_RAY_DISTANCE`, `GET_RAY_HIT_OBJECT`, `GET_RAY_HIT_X/Y/Z`, `GET_RAY_HIT_NORMAL_X/Y/Z`, `RAY_DID_HIT`, `RAY_DID_HIT2`, `RAY_HIT_SPRITE_NAME`, `RAY_HIT_X`, `RAY_HIT_Y`, `RAY_HIT_DISTANCE` |
| Объекты по ID | `ID_OF_DETECTED_OBJECT`, `OBJECT_WITH_ID_VISIBLE` |
| Нейросети (PT = PyTorch-подобный тензор) | `PT_ARGMAX`, `PT_VALUE`, `PT_VALUEND`, `PT_SHAPE`, `PT_DUMP`, `PT_TOTALSIZE`, `PT_SAMPLE` |
| Fast2D (быстрый 2D-движок) | `F2D_X`, `F2D_Y`, `F2D_ROTATION`, `F2D_SCALE_X`, `F2D_SCALE_Y`, `F2D_COLOR_R/G/B`, `F2D_ALPHA`, `F2D_TEXTURE`, `F2D_CAM_X`, `F2D_CAM_Y`, `F2D_CAM_ZOOM`, `F2D_IS_TOUCHED`, `F2D_IS_TOUCHED_INDEX` |
| Камера 2D | `CAMERA_X`, `CAMERA_Y`, `CAMERA_ROTATION`, `CAMERA_ZOOM` |
| Воксели | `VOXEL_GET_ID`, `VOXEL_GET_DATA` |
| Сеть и системные события | `HTTP_RESPONSE_TEXT`, `HTTP_RESPONSE_CODE`, `HTTP_RESPONSE_HEADER`, `MQTT_MESSAGE`, `NOTIFICATION_REPLY`, `CLIPBOARD_TEXT` |
| Arduino / Raspberry Pi | `ARDUINOANALOG`, `ARDUINODIGITAL`, `RASPIDIGITAL` |

Служебные наборы в `Functions.java`:
- `TEXT` — функции, возвращающие строку (в него входят почти все строковые, файловые, 3D-, Fast2D-, HTTP- и PT-функции);
- `LIST` — функции работы со списками (первый аргумент — узел `USER_LIST`);
- `BOOLEAN` — `TRUE`, `FALSE`, `CONTAINS`, `MULTI_FINGER_TOUCHED`, `COLLIDES_WITH_COLOR`, `COLOR_TOUCHES_COLOR`, `COLOR_EQUALS_COLOR`, `RAY_DID_HIT`, `OBJECT_INTERSECTS_OBJECT`, `OBJECT_TOUCHES_OBJECT`, `JSON_IS_VALID`.

Класс помечен `@LunoClass` — enum доступен и из встроенного языка LunoScript.

### 6.9. Операторы (`Operators.java`)

В `code.xml` это узел `<type>OPERATOR</type><value>ИМЯ</value>` с `leftChild` и `rightChild` (если `leftChild` отсутствует, оператор считается унарным и берёт операнд из `rightChild`; унарными работают только `MINUS` и `LOGICAL_NOT`, подробности в 6.13).

| Оператор | Приоритет | Логический | Смысл |
|---|---|---|---|
| `LOGICAL_OR` | 1 | да | ИЛИ |
| `LOGICAL_AND` | 2 | да | И |
| `EQUAL` | 3 | да | равно |
| `NOT_EQUAL` | 4 | да | не равно |
| `SMALLER_OR_EQUAL` | 4 | да | меньше или равно |
| `GREATER_OR_EQUAL` | 4 | да | больше или равно |
| `SMALLER_THAN` | 4 | да | меньше |
| `GREATER_THAN` | 4 | да | больше |
| `LOGICAL_NOT` | 4 | да | отрицание |
| `PLUS` | 5 | нет | сложение |
| `MINUS` | 5 | нет | вычитание |
| `STRING_CONCAT` | 5 | нет | склейка строк |
| `MULT` | 6 | нет | умножение |
| `DIVIDE` | 6 | нет | деление |
| `MOD` | 6 | нет | остаток от деления |
| `POW` | 7 | нет | степень |

Чем больше число приоритета, тем раньше выполняется операция.

### 6.10. Типы токенов формулы (`InternTokenType.java`)

`InternTokenType` — это enum **внутреннего парсера формул** (редактор формул и разбор строки в дерево), а не прямой список значений `<type>` в XML. Значения: `NUMBER`, `OPERATOR`, `FUNCTION_NAME`, `BRACKET_OPEN`, `BRACKET_CLOSE`, `SENSOR`, `FUNCTION_PARAMETERS_BRACKET_OPEN`, `FUNCTION_PARAMETERS_BRACKET_CLOSE`, `FUNCTION_PARAMETER_DELIMITER`, `PERIOD`, `USER_VARIABLE`, `USER_LIST`, `USER_DEFINED_BRICK_INPUT`, `COLLISION_FORMULA`, `STRING`, `PARSER_END_OF_FILE`.

Соответствие с XML: реальный список значений `<type>` задаёт не этот enum, а `FormulaElement.ElementType` (см. 6.13). Имена `NUMBER`, `OPERATOR`, `SENSOR`, `USER_VARIABLE`, `USER_LIST`, `STRING`, `USER_DEFINED_BRICK_INPUT`, `COLLISION_FORMULA` совпадают; вместо `FUNCTION_NAME` в XML пишется `FUNCTION`, вместо пары `BRACKET_OPEN`/`BRACKET_CLOSE` — один узел `BRACKET`. Разделители параметров функций и `PERIOD` в XML не хранятся — структуру задаёт дерево.

### 6.11. Типы скриптов (`script/@type`)

Список классов `*Script` из дерева проекта (пакет `content`), имя класса совпадает со значением `<script type="...">`: `StartScript`, `WhenScript`, `WhenTouchDownScript`, `WhenConditionScript`, `WhenBackgroundChangesScript`, `WhenBounceOffScript`, `WhenClonedScript`, `WhenClonedWithNameScript`, `WhenSpriteReleasedScript`, `WhenFingerMovedOnScreenScript`, `WhenFingerMovedOverSpriteScript`, `WhenGamepadButtonScript`, `WhenMouseButtonClickedScript`, `WhenMouseWheelScrolledScript`, `WhenNfcScript`, `WhenMqttMessageScript`, `WhenNotificationClickedScript`, `WhenNotificationActionTriggeredScript`, `WhenAppMinimizedScript`, `WhenAppRestoredScript`, `WhenWindowResizedScript`, `BroadcastScript`, `BroadcastWithParamsReceiverScript`, `RaspiInterruptScript`, `BeforeUpdateScript`, `AfterUpdateScript`, `BackPressedScript`, `ExitProjectScript`, `UserDefinedScript`, `EmptyScript`. Базовый класс — `Script`.

Это перечень по именам файлов, содержимое классов я не видел, поэтому поля конкретных скриптов (например, `spriteToBounceOffName` у `WhenBounceOffScript`) здесь не описаны.

### 6.12. Устаревший формат и миграция (`BackwardCompatibleCatrobatLanguageXStream.java`)

Этот класс читает **старые** проекты и приводит их к современному виду. Он не определяет современный формат, но прямо подтверждает его структуру: в новом формате скрипт это `<script type="ИмяКласса">`, блок это `<brick type="ИмяКласса">`, формула это `<formula category="ПОЛЕ">` внутри `<formulaList>`.

**Как устроен старый формат**
- Скрипты и блоки были отдельными тегами в lowerCamelCase: `<startScript>`, `<setXBrick>`, `<askBrick>` и т. д.
- Параметры блока были тегами со старыми именами (`xPosition`, `steps`, `durationInSeconds`), внутри них лежал `<formulaTree>`.
- Миграция превращает тег в `<brick type="SetXBrick">`, а `<formulaTree>` в `<formula category="X_POSITION">`, подставляя нужное значение `BrickField`.
- Таблица миграции охватывает 141 тип блока. Для большинства имя нового класса получается из старого тега заменой первой буквы на заглавную.

**Нерегулярные переименования блоков** (старый тег → новый `type`)

| Старый тег | Новый `brick/@type` |
|---|---|
| `setGhostEffectBrick` | `SetTransparencyBrick` |
| `changeGhostEffectByNBrick` | `ChangeTransparencyByNBrick` |
| `setSpeechLanguageBrick` | `SetListeningLanguageBrick` |
| `videoBrick` | `CameraBrick` |
| `collisionReceiverBrick` | `WhenBounceOffBrick` |
| `phiroSensorBrick` | `PhiroIfLogicBeginBrick` |
| `phiroSensorElseBrick` | `IfLogicElseBrick` |
| `phiroSensorEndBrick` | `IfLogicEndBrick` |
| `droneTakeOffBrick` | `DroneTakeOffLandBrick` |
| `droneGoEmergencyBrick`, `droneEmergencyBrick` | `DroneEmergencyBrick` |
| `particleEffectAdditiveBrick` | `ParticleEffectAdditivityBrick` |
| `legoNxtMotorActionBrick` | `LegoNxtMotorMoveBrick` |

**Старые теги скриптов → `script/@type`**: `startScript` → `StartScript`, `whenScript` → `WhenScript`, `whenConditionScript` → `WhenConditionScript`, `whenBackgroundChangesScript` → `WhenBackgroundChangesScript`, `broadcastScript` → `BroadcastScript`, `raspiInterruptScript` → `RaspiInterruptScript`, `whenNfcScript` → `WhenNfcScript`, `collisionScript` → `WhenBounceOffScript`, `whenTouchDownScript` → `WhenTouchDownScript`, `whenGamepadButtonScript` → `WhenGamepadButtonScript`, `userDefinedScript` → `UserDefinedScript`.

**Примеры соответствия старого поля новому `BrickField`** (то, что стало значением `formula/@category`)

| Блок | Старое поле → `BrickField` |
|---|---|
| `SetXBrick` | `xPosition` → `X_POSITION` |
| `PlaceAtBrick` | `xPosition` → `X_POSITION`, `yPosition` → `Y_POSITION` |
| `GlideToBrick` | `xDestination` → `X_DESTINATION`, `yDestination` → `Y_DESTINATION`, `durationInSeconds` → `DURATION_IN_SECONDS` |
| `ChangeXByNBrick` | `xMovement` → `X_POSITION_CHANGE` |
| `SetVariableBrick` | `variableFormula` → `VARIABLE` |
| `ChangeVariableBrick` | `variableFormula` → `VARIABLE_CHANGE` |
| `WaitBrick` | `timeToWaitInSeconds` → `TIME_TO_WAIT_IN_SECONDS` |
| `RepeatBrick` | `timesToRepeat` → `TIMES_TO_REPEAT` |
| `IfLogicBeginBrick` | `ifCondition` → `IF_CONDITION` |
| `SayForBubbleBrick` | `text` → `STRING`, `durationInSeconds` → `DURATION_IN_SECONDS` |
| `SpeakBrick` | `text` → `SPEAK` |
| `SetGravityBrick` | `gravityX` → `PHYSICS_GRAVITY_X`, `gravityY` → `PHYSICS_GRAVITY_Y` |
| `SetPenColorBrick` | `penColor` → `PEN_COLOR_RED/GREEN/BLUE` |
| `DroneMoveForwardBrick` | `timeToFlyInSeconds` → `DRONE_TIME_TO_FLY_IN_SECONDS`, `powerInPercent` → `DRONE_POWER_IN_PERCENT` |

**Прочие миграции, которые выполняет класс**
- Дочерние теги `name` у `lookList` и `object` превращаются в **атрибуты** `name`.
- Корневой узел `variables` переименовывается в `data`.
- Удаляются устаревшие `isPhiroProProject`, `inUserBrick` и служебные вложенные `object`.
- Для блоков `SPEAK` и `NOTE` текст оборачивается в формулу `<type>STRING</type><value>…</value>`.
- Скрипт `CollisionScript` получает тип `WhenBounceOffScript`, поля `receivedMessage` и `spriteToCollideWithName` переименовываются в `spriteToBounceOffName`.
- Для LEGO NXT мотор `MOTOR_A_C` заменяется на `MOTOR_B_C`.
- У `CameraBrick` и `ChooseCameraBrick` поле `spinnerSelectionID` (0 или 1) заменяется на `spinnerSelectionON` и `spinnerSelectionFRONT` со значениями `false`/`true`.
- Ссылки `reference="..."` пересчитываются под новую структуру.
- Если чтение проекта падает с `ConversionException`, класс сначала запускает эту миграцию и пробует загрузить файл ещё раз.

Для разбора **современных** файлов эта таблица нужна только как справка по историческим именам; в актуальных `code.xml` старых тегов быть не должно.

### 6.13. Дерево формул и его вычисление (`FormulaElement.java`)

`FormulaElement` — один узел дерева формулы. Он соответствует элементу `<formula>` и вложенным `<leftChild>`, `<rightChild>`, `<additionalChildren>` в XML. У узла есть `type`, `value`, `leftChild`, `rightChild` и список `additionalChildren`.

**Все допустимые значения `<type>` (enum `ElementType`)**

| `type` | Что хранится в `value` | Дочерние узлы |
|---|---|---|
| `NUMBER` | число в виде текста (`"5"`, `"0.5"`) | нет |
| `STRING` | строка как есть | нет |
| `OPERATOR` | имя из `Operators` (6.9) | `leftChild` и `rightChild`; для унарного только `rightChild` |
| `FUNCTION` | имя из `Functions` (6.8) либо имя пользовательской функции | аргументы, см. ниже |
| `SENSOR` | имя из `Sensors` (6.7) | нет |
| `USER_VARIABLE` | имя переменной | нет |
| `USER_LIST` | имя списка | нет |
| `USER_DEFINED_BRICK_INPUT` | имя входного параметра пользовательского блока | нет |
| `BRACKET` | пусто | скобки: внутри лежит выражение |
| `COLLISION_FORMULA` | имя второго объекта, с которым проверяется столкновение | нет |

Это закрывает вопрос из 6.10: в XML скобки хранятся как узел `BRACKET`.

**Куда попадают аргументы функции**

| Позиция аргумента | Где лежит в XML |
|---|---|
| 1-й | `leftChild` |
| 2-й | `rightChild` |
| 3-й | `additionalChildren`, первый элемент |
| 4-й | `additionalChildren`, второй элемент |

Исключения и особые случаи:
- `IF_THEN_ELSE`: `leftChild` — условие, `rightChild` — значение при истине, `additionalChildren[0]` — значение при лжи.
- `JOIN3`: три строки в `leftChild`, `rightChild`, `additionalChildren[0]`.
- `DISTAN` использует четыре аргумента, `CLAMP` и `SUBTEXT` три.
- Функции списков принимают узел `USER_LIST` на строго определённой позиции: `LIST_ITEM(индекс, список)` — список в `rightChild`; `INDEX_OF_ITEM(значение, список)` — список в `rightChild`; `CONTAINS(список, значение)`, `NUMBER_OF_ITEMS(список)`, `CONNECT(список, …)`, `FLATTEN(список)` и `FIND(список, …)` — список в `leftChild`.
- Для `BRACKET` результат берётся из последнего элемента `additionalChildren`, а если его нет, то из `rightChild`.

**Типы значений и приведение**
- Числа хранятся как `Double`, строки как `String`. Логических значений нет: истина это `1.0`, ложь это `0.0`, а любое число, не равное `0`, считается истиной.
- `NUMBER` с текстом, который нельзя разобрать как число, возвращается как строка.
- Арифметика работает с числами; нечисловой или отсутствующий операнд принимается за `0`. Если хотя бы один операнд `NaN`, результат тоже `NaN`.
- Деление на `0` даёт `NaN`, а не ошибку.
- `EQUAL` и `NOT_EQUAL` сравнивают значения с учётом типов через отдельную функцию, остальные сравнения идут по числам.
- `STRING_CONCAT` превращает операнды в строки: `null` и `NaN` дают пустую строку, число `5.0` записывается как `5`.

**Неизвестные значения и ошибки**
- Неизвестный оператор в `value` даёт `false`.
- Значение `FUNCTION`, которого нет в `Functions`, ищется среди **пользовательских формул** (`CustomFormulaManager`, они пишутся на LunoScript) по уникальному имени. Аргументы передаются в том же порядке: `leftChild`, `rightChild`, затем `additionalChildren`. Если такой формулы нет, результат `0`.
- Поэтому незнакомый `FUNCTION` в чужом `code.xml` не обязательно ошибка: это может быть вызов пользовательской формулы.
- Функции без зарегистрированной реализации возвращают `0`.

**Имена, разрешаемые во время выполнения**
- `USER_VARIABLE`, `USER_LIST`, `USER_DEFINED_BRICK_INPUT` ищутся по имени в текущей области видимости (`Scope`) при каждом выполнении, значение кешируется для конкретной области.
- Для `COLLISION_FORMULA` старые проекты хранили имя столкновения в другом виде; при загрузке значение приводится к имени второго объекта (`updateCollisionFormulaToVersion`).

**Провайдеры функций**
Часть функций реализована не в самом `FormulaElement`, а в провайдерах (`function/`): `MathFunctionProvider`, `TouchFunctionProvider`, `TextBlockFunctionProvider`, `ArduinoFunctionProvider`, `RaspiFunctionProvider`, `ObjectDetectorFunctionProvider`. Остальные (`RAND`, `IF_THEN_ELSE`, строки, списки, файлы, JSON, 3D и т. д.) разобраны прямо в `FormulaElement`. Для разбора `code.xml` это различие не важно, оно нужно только тем, кто будет искать реализацию конкретной функции.

### 6.14. Русские названия и примеры параметров функций (`strings.xml`)

Файл `strings.xml` (русская локализация) содержит **отображаемые** имена функций и датчиков и примеры вызова. Описаний в виде текста («что делает функция») там нет, только названия и примеры. Важное правило для разбора: в `code.xml` в `<value>` всегда хранится **имя константы enum** (например, `SIN`, `JSON_GET`), а не русское название из таблицы. Русское название нужно только для понимания смысла и для сопоставления с тем, что пользователь видит в редакторе.

Ключи в `strings.xml` построены по трём схемам: `formula_editor_function_<имя>` (+ `_parameter`), `formula_<имя>` (+ `_param`) и отдельные ключи без префикса для части функций (`view_x`, `video_time`, `is_video_playing`). Сопоставление ниже сделано по этим ключам; часть имён пришлось сопоставлять вручную по смыслу (например, `GET_3D_ROTATION_YAW` соответствует ключу `formula_3d_rot_yaw`). Пример параметров показывает порядок аргументов так, как его видит пользователь; для функций без примера параметры в строках не заданы.

Особенности, которые нужно учитывать:
- Разные константы могут иметь одинаковое русское название: например, `FINGER_X` и `MULTI_FINGER_X` оба показываются как «касание_к_экрану_по_X», а `OBJECT_WIDTH` и `WIDTH` как «ширина».
- Некоторые русские названия не совпадают по смыслу с именем константы: `GET_3D_ROTATION_YAW` называется «3D_вращение_y», а `GET_3D_ROTATION_PITCH` «3D_вращение_x» (оси названы по-своему).
- Пары `GET_RAY_HIT_X`/`RAY_HIT_X` и `RAY_DID_HIT`/`RAY_DID_HIT2` существуют как отдельные функции с разными названиями («луч_x» и «луч_точка_x», «луч_столкнулся» и «луч_попал»).

| `value` в XML | Название в редакторе (ru) | Пример параметров |
|---|---|---|
| `SIN` | `синус` | `(90)` |
| `COS` | `косинус` | `(360)` |
| `TAN` | `тангенс` | `(45)` |
| `LN` | `натуральный_логарифм` | `(2.718281828459)` |
| `LOG` | `десятичный_логарифм` | `(10)` |
| `SQRT` | `корень` | `(4)` |
| `RAND` | `случайное_значение_от_до` | `(1,6)` |
| `ROUND` | `округлить` | `(1.6)` |
| `ROUNDTO` | `округлить_до` | `(123.456, 1)` |
| `ABS` | `абсолютное_значение` | `(1)` |
| `PI` | `Пи` | — |
| `MOD` | `остаток_от_деления` | `(3,2)` |
| `ARCSIN` | `арксинус` | `(0.5)` |
| `ARCCOS` | `арккосинус` | `(0)` |
| `ARCTAN` | `арктангенс` | `(1)` |
| `ARCTAN2` | `арктангенс2` | `(-1, 0)` |
| `EXP` | `экспонента` | `(1)` |
| `POWER` | `степень` | `(2,3)` |
| `FLOOR` | `округлить_к_меньшему` | `(0.7)` |
| `CEIL` | `округлить_к_большему` | `(0.3)` |
| `MAX` | `максимум` | `(5,4)` |
| `MIN` | `минимум` | `(7,2)` |
| `TRUE` | `истина` | — |
| `FALSE` | `ложь` | — |
| `LENGTH` | `длина` | `('hello world')` |
| `LETTER` | `символ` | `(1,'hello world')` |
| `SUBTEXT` | `обрезать` | `(3,5,'hello         world')` |
| `FILE` | `файл_проекта` | `('variable.txt')` |
| `TO_HEX` | `в_HEX` | `(175)` |
| `TO_DEC` | `из_HEX` | `('AF')` |
| `CLAMP` | `ограничить` | `(-2,2,10)` |
| `DISTAN` | `расстояние` | `(100, 200, -100, 200)` |
| `UPPER` | `верхний_регистр` | `('aboudna')` |
| `LOWER` | `нижний_регистр` | `('SIGMA')` |
| `REVERSE` | `отразить` | `('olleH')` |
| `VAR` | `локальная_переменная` | `('variable1')` |
| `VARNAME` | `название_локальной_переменной` | `(0)` |
| `VARVALUE` | `значение_локальной_переменной` | `(0)` |
| `RANDOM_STR` | `случайная_строка` | `(15)` |
| `REPLACE` | `заменить` | `('pandas love bamboo','love','eat')` |
| `CONTAINS_STR` | `строка_содержит` | `('bats are cutest!','cute')` |
| `REPEAT` | `повторить_текст` | `('повторение - признак безумия ', 10)` |
| `TABLE_X` | `размер_x_таблицы` | `('myTable')` |
| `TABLE_Y` | `размер_Y_таблицы` | `('myTable')` |
| `TABLE_ELEMENT` | `элемент_таблицы` | `('myTable', 3, 2)` |
| `TABLE_JOIN` | `соединить_таблицу_через` | `('myTable', ',', '\n')` |
| `JOIN` | `соединить` | `('hello',' world')` |
| `JOIN3` | `соединить` | `('hello',' world','!')` |
| `DISTANCE` | `расстояние_левенштейна` | `('panda', 'lavanda')` |
| `JOINNUMBER` | `соединить_цифры` | `(1,1)` |
| `REGEX` | `регулярное_выражение` | `(' an? ([^ .]+)','I am a panda.')` |
| `LIST_ITEM` | `элемент` | `(1,*название списка*)` |
| `CONTAINS` | `содержит` | `(*название списка*,1)` |
| `INDEX_OF_ITEM` | `индекс_элемента` | `(1,*название списка*)` |
| `NUMBER_OF_ITEMS` | `количество_элементов` | `(*название списка*)` |
| `LUA` | `lua` | `('return math.sqrt(25)')` |
| `FLOATARRAY` | `размер_FloatArray` | `('FloatArray')` |
| `VIEW_X` | `позиция_x_view` | — |
| `VIEW_Y` | `позиция_y_view` | — |
| `VIEW_WIDTH` | `ширина_view` | — |
| `VIEW_HEIGHT` | `высота_view` | — |
| `VIDEO_PLAYING` | `videoplayer_запущен` | — |
| `VIDEO_TIME` | `время_videoplayer` | — |
| `JSON_GET` | `json_получить` | `('{"id":1}', 'id')` |
| `JSON_SET` | `json_задать` | `('{"id":1}', 'id'; 2)` |
| `JSON_IS_VALID` | `json_валидный` | `('{"id":1}')` |
| `ARDUINOANALOG` | `аналоговый_пин_arduino` | — |
| `ARDUINODIGITAL` | `цифровой_пин_arduino` | — |
| `RASPIDIGITAL` | `пин         raspberry pi` | — |
| `MULTI_FINGER_X` | `касание_к_экрану_по_X` | — |
| `MULTI_FINGER_Y` | `касание_к_экрану_по_Y` | — |
| `MULTI_FINGER_TOUCHED` | `касается_экрана` | — |
| `INDEX_CURRENT_TOUCH` | `индекс_текущего_касания` | — |
| `COLLIDES_WITH_COLOR` | `касается_цвета` | — |
| `COLOR_TOUCHES_COLOR` | `цвет_касается_цвета` | — |
| `COLOR_AT_XY` | `цвет_на_X_и_Y` | — |
| `COLOR_EQUALS_COLOR` | `цвет_равен_цвету_с_допустимостью_в_%` | — |
| `TEXT_BLOCK_X` | `текстовый блок по оси X с камеры` | — |
| `TEXT_BLOCK_Y` | `текстовый блок по оси Y с камеры` | — |
| `TEXT_BLOCK_SIZE` | `размер текстового блока с камеры` | — |
| `TEXT_BLOCK_FROM_CAMERA` | `текстовый блок с камеры` | — |
| `TEXT_BLOCK_LANGUAGE_FROM_CAMERA` | `текстовый блок языка с камеры` | — |
| `IF_THEN_ELSE` | `если_то_иначе` | `(ложь, 2, 3)` |
| `FLATTEN` | `выравнивание` | `(*название списка*)` |
| `CONNECT` | `соединить_элементы` | `(*название списка*, ',')` |
| `FIND` | `найти` | `(*название списка*, '256')` |
| `TOUCHES_OBJECT_BY_NAME` | `касается_объекта_по_имени` | `("имя объекта")` |
| `GET_3D_POSITION_X` | `3D_позиция_x` | — |
| `GET_3D_POSITION_Y` | `3D_позиция_y` | — |
| `GET_3D_POSITION_Z` | `3D_позиция_z` | — |
| `GET_3D_ROTATION_YAW` | `3D_вращение_y` | — |
| `GET_3D_ROTATION_PITCH` | `3D_вращение_x` | — |
| `GET_3D_ROTATION_ROLL` | `3D_вращение_z` | — |
| `GET_3D_SCALE_X` | `3D_размер_x` | — |
| `GET_3D_SCALE_Y` | `3D_размер_y` | — |
| `GET_3D_SCALE_Z` | `3D_размер_z` | — |
| `GET_3D_DISTANCE` | `3D_расстояние_между` | — |
| `GET_DIRECTION_X` | `направление_X_из_угла` | — |
| `GET_DIRECTION_Y` | `направление_Y_из_угла` | — |
| `GET_ANGLE` | `угол_из_направления` | `(0.6, 1)` |
| `GET_RAY_DISTANCE` | `длина_луча` | — |
| `GET_RAY_HIT_OBJECT` | `объект_луча` | — |
| `GET_CAMERA_POS_X` | `позиция_камеры_X` | — |
| `GET_CAMERA_POS_Y` | `позиция_камеры_Y` | — |
| `GET_CAMERA_POS_Z` | `позиция_камеры_Z` | — |
| `GET_CAMERA_DIR_X` | `направление_камеры_X` | — |
| `GET_CAMERA_DIR_Y` | `направление_камеры_Y` | — |
| `GET_CAMERA_DIR_Z` | `направление_камеры_Z` | — |
| `GET_CAMERA_ROTATION_YAW` | `вращение_камеры_Y` | — |
| `GET_CAMERA_ROTATION_PITCH` | `вращение_камеры_X` | — |
| `GET_CAMERA_ROTATION_ROLL` | `вращение_камеры_Z` | — |
| `GET_3D_VELOCITY_X` | `3D_скорость_X` | — |
| `GET_3D_VELOCITY_Y` | `3D_скорость_Y` | — |
| `GET_3D_VELOCITY_Z` | `3D_скорость_Z` | — |
| `OBJECT_TOUCHES_OBJECT` | `объект_касается_объекта` | `('ID объекта 1', 'ID объекта 2')` |
| `OBJECT_INTERSECTS_OBJECT` | `объект_пересекает_объект` | `('ID объекта 1', 'ID объекта 2')` |
| `GET_RAY_HIT_X` | `луч_x` | `("id_луча")` |
| `GET_RAY_HIT_Y` | `луч_y` | `("id_луча")` |
| `GET_RAY_HIT_Z` | `луч_z` | — |
| `GET_RAY_HIT_NORMAL_X` | `нормаль_луча_x` | — |
| `GET_RAY_HIT_NORMAL_Y` | `нормаль_луча_y` | — |
| `GET_RAY_HIT_NORMAL_Z` | `нормаль_луча_z` | — |
| `RAY_DID_HIT` | `луч_столкнулся` | `("id_луча")` |
| `ID_OF_DETECTED_OBJECT` | `ID обнаруженного объекта` | — |
| `OBJECT_WITH_ID_VISIBLE` | `Объект с ID виден` | — |
| `IS_MOUSE_BUTTON_DOWN` | `кнопка_мыши_нажата` | `('Левая')` |
| `RAY_DID_HIT2` | `луч_попал` | — |
| `RAY_HIT_SPRITE_NAME` | `луч_имя_спрайта` | `("id_луча")` |
| `RAY_HIT_X` | `луч_точка_x` | — |
| `RAY_HIT_Y` | `луч_точка_y` | — |
| `RAY_HIT_DISTANCE` | `луч_дистанция` | `("id_луча")` |
| `FILES_PATH` | `все_файлы_проекта` | — |
| `ALL_FILES` | `путь_к_файлам_проекта` | — |
| `FILE_SIZE` | `размер_файла_проекта` | — |
| `DELTA` | `дельта-тайм` | — |
| `COLLISION_LIST` | `список_столкновений_объекта` | — |
| `INTERSECT_LIST` | `список_пересечений_объекта` | — |
| `PT_ARGMAX` | `PT_argmax` | — |
| `PT_VALUE` | `PT_значение` | — |
| `PT_VALUEND` | `PT_значение_ND` | — |
| `PT_SHAPE` | `PT_размер` | — |
| `PT_DUMP` | `PT_в_строку` | — |
| `PT_TOTALSIZE` | `PT_длина` | — |
| `F2D_X` | `F2D_X` | — |
| `F2D_Y` | `F2D_Y` | — |
| `F2D_ROTATION` | `F2D_вращение` | — |
| `F2D_SCALE_X` | `F2D_ширина` | — |
| `F2D_SCALE_Y` | `F2D_высота` | — |
| `F2D_COLOR_R` | `F2D_цвет_R` | — |
| `F2D_COLOR_G` | `F2D_цвет_G` | — |
| `F2D_COLOR_B` | `F2D_цвет_B` | — |
| `F2D_ALPHA` | `F2D_alpha` | — |
| `F2D_TEXTURE` | `F2D_текстура` | — |
| `F2D_CAM_X` | `F2D_камера_X` | — |
| `F2D_CAM_Y` | `F2D_камера_Y` | — |
| `F2D_CAM_ZOOM` | `F2D_камера_zoom` | — |
| `F2D_IS_TOUCHED` | `F2D_объект_нажат` | `('id')` |
| `F2D_IS_TOUCHED_INDEX` | `F2D_объект_нажат_пальцем` | `('id', 0)` |
| `VOXEL_GET_ID` | `Voxel_получить_id` | `('worldId', x, y, z)` |
| `VOXEL_GET_DATA` | `Voxel_получить_данные` | `('worldId', x, y, z)` |
| `HTTP_RESPONSE_TEXT` | `http_текст_ответа` | `('id')` |
| `HTTP_RESPONSE_CODE` | `http_код_ответа` | `('id')` |
| `HTTP_RESPONSE_HEADER` | `http_заголовок_ответа` | `('id', 'header_name')` |
| `NOTIFICATION_REPLY` | `ввод_из_уведомления` | `('action_id')` |
| `READ_FILE` | `прочитать_файл` | `('file.txt')` |
| `MEDIA_DURATION` | `длительность_медиа` | `('audio.mp3')` |
| `IMAGE_WIDTH` | `ширина_изображения` | `('image.png')` |
| `IMAGE_HEIGHT` | `высота_изображения` | `('image.png')` |
| `FILE_LAST_MODIFIED` | `файл_изменен` | `('file.txt')` |
| `CAMERA_X` | `камера_x` | — |
| `CAMERA_Y` | `камера_y` | — |
| `CAMERA_ROTATION` | `камера_вращение` | — |
| `CAMERA_ZOOM` | `камера_зум` | — |
| `CLIPBOARD_TEXT` | `текст_буфера_обмена` | — |
| `MQTT_MESSAGE` | `mqtt_сообщение` | `('имя_комнаты')` |
| `FILE_TO_BASE64` | `файл_в_base64` | `('имя_файла')` |
| `MD5` | `md5` | `('текст')` |
| `SHA256` | `sha256` | `('текст')` |
| `FILE_MD5` | `файл_md5` | `('имя_файла')` |
| `FILE_SHA256` | `файл_sha256` | `('имя_файла')` |
| `PT_SAMPLE` | `PT_выбрать_действие` | `('тензор')` |
| `CHAR_TO_UNICODE` | `символ_в_юникод` | `('A')` |
| `UNICODE_TO_CHAR` | `юникод_в_символ` | `(65)` |
| `UNESCAPE_UTF` | `декодировать_utf` | `('\u0430')` |

### 6.15. Русские названия датчиков и свойств объекта (`strings.xml`)

Те же правила, что в 6.14: в XML пишется имя константы из `Sensors`, русское название нужно для понимания. Ключи — `formula_editor_sensor_<имя>`, `formula_editor_object_<имя>` (свойства объекта), `formula_editor_phiro_sensor_<имя>`, `formula_editor_nfc_<имя>`, а часть имён сопоставлена вручную (`MOTION_DIRECTION` → «направление_движения», `LOOK_DIRECTION` → «направление_взгляда»).

Для значений `TEXT_BLOCK_X`, `TEXT_BLOCK_Y`, `TEXT_BLOCK_SIZE`, `TEXT_BLOCK_FROM_CAMERA`, `TEXT_BLOCK_LANGUAGE_FROM_CAMERA` в таблице датчиков названий нет: эти имена одновременно есть в `Functions` (6.14), и русские строки заданы для функций. Для `FPS` русского названия среди ключей формул я не нашёл.

| `value` в XML | Название в редакторе (ru) |
|---|---|
| `X_ACCELERATION` | `ускорение_по_оси_X` |
| `Y_ACCELERATION` | `ускорение_по_оси_Y` |
| `Z_ACCELERATION` | `ускорение_по_оси_Z` |
| `COMPASS_DIRECTION` | `направление_компаса` |
| `X_INCLINATION` | `наклон_по_оси_X` |
| `Y_INCLINATION` | `наклон_по_оси_Y` |
| `LOUDNESS` | `громкость` |
| `LATITUDE` | `широта` |
| `LONGITUDE` | `долгота` |
| `LOCATION_ACCURACY` | `точность_расстояния` |
| `ALTITUDE` | `высота` |
| `USER_LANGUAGE` | `язык_пользователя` |
| `TIMER` | `таймер` |
| `DATE_YEAR` | `год` |
| `DATE_MONTH` | `месяц` |
| `DATE_DAY` | `день` |
| `DATE_WEEKDAY` | `день_недели` |
| `TIME_HOUR` | `час` |
| `TIME_MINUTE` | `минута` |
| `TIME_SECOND` | `секунда` |
| `FACE_DETECTED` | `видно_первое_лицо` |
| `FACE_SIZE` | `размер_первого_лица` |
| `FACE_X` | `первое_лицо_по_оси_X` |
| `FACE_Y` | `первое_лицо_по_оси_Y` |
| `SECOND_FACE_DETECTED` | `видно_второе_лицо` |
| `SECOND_FACE_SIZE` | `размер_второго_лица` |
| `SECOND_FACE_X` | `второе_лицо_по_оси_X` |
| `SECOND_FACE_Y` | `второе_лицо_по_оси_Y` |
| `HEAD_TOP_X` | `верхняя_часть_головы_по_оси_X` |
| `HEAD_TOP_Y` | `верх_головы_по_оси_Y` |
| `NECK_X` | `шея_по_оси_X` |
| `NECK_Y` | `шея_по_оси_Y` |
| `NOSE_X` | `нос_по_оси_X` |
| `NOSE_Y` | `нос_по_оси_Y` |
| `LEFT_EYE_INNER_X` | `внутренний_угол_левого_глаза_по_оси_X` |
| `LEFT_EYE_INNER_Y` | `внутренний_угол_левого_глаза_по_оси_Y` |
| `LEFT_EYE_CENTER_X` | `центр_левого_глаза_по_оси_X` |
| `LEFT_EYE_CENTER_Y` | `центр_левого_глаза_по_оси_Y` |
| `LEFT_EYE_OUTER_X` | `внешний_угол_левого_глаза_по_оси_X` |
| `LEFT_EYE_OUTER_Y` | `внешний_угол_левого_глаза_по_оси_Y` |
| `RIGHT_EYE_INNER_X` | `внутренний_угол_правого_глаза_по_оси_X` |
| `RIGHT_EYE_INNER_Y` | `внутренний_угол_правого_глаза_по_оси_Y` |
| `RIGHT_EYE_CENTER_X` | `центр_правого_глаза_по_оси_X` |
| `RIGHT_EYE_CENTER_Y` | `центр_правого_глаза_по_оси_Y` |
| `RIGHT_EYE_OUTER_X` | `наружный угол правого глаза по оси X` |
| `RIGHT_EYE_OUTER_Y` | `наружный угол правого глаза по оси Y` |
| `LEFT_EAR_X` | `левое ухо по оси X` |
| `LEFT_EAR_Y` | `левое ухо по оси Y` |
| `RIGHT_EAR_X` | `правое ухо по оси X` |
| `RIGHT_EAR_Y` | `правое ухо по оси Y` |
| `MOUTH_LEFT_CORNER_X` | `левый угол рта по оси X` |
| `MOUTH_LEFT_CORNER_Y` | `левый угол рта по оси Y` |
| `MOUTH_RIGHT_CORNER_X` | `правый угол рта по оси X` |
| `MOUTH_RIGHT_CORNER_Y` | `правый угол рта по оси Y` |
| `LEFT_SHOULDER_X` | `левое плечо по оси X` |
| `LEFT_SHOULDER_Y` | `левое плечо по оси Y` |
| `RIGHT_SHOULDER_X` | `правое плечо по оси X` |
| `RIGHT_SHOULDER_Y` | `правое плечо по оси Y` |
| `LEFT_ELBOW_X` | `левый локоть по оси X` |
| `LEFT_ELBOW_Y` | `левый локоть по оси Y` |
| `RIGHT_ELBOW_X` | `правый локоть по оси X` |
| `RIGHT_ELBOW_Y` | `правый локоть по оси Y` |
| `LEFT_WRIST_X` | `левое запястье по оси X` |
| `LEFT_WRIST_Y` | `левое запястье по оси Y` |
| `RIGHT_WRIST_X` | `правое запястье по оси X` |
| `RIGHT_WRIST_Y` | `правое запястье по оси Y` |
| `LEFT_PINKY_X` | `сустав мизинца левой руки по оси X` |
| `LEFT_PINKY_Y` | `сустав мизинца левой руки по оси Y` |
| `RIGHT_PINKY_X` | `сустав мизинца правой руки по оси X` |
| `RIGHT_PINKY_Y` | `сустав мизинца правой руки по оси Y` |
| `LEFT_INDEX_X` | `сустав указательного пальца левой руки по оси X` |
| `LEFT_INDEX_Y` | `сустав указательного пальца левой руки по оси Y` |
| `RIGHT_INDEX_X` | `сустав указательного пальца правой руки по оси X` |
| `RIGHT_INDEX_Y` | `сустав указательного пальца правой руки по оси Y` |
| `LEFT_THUMB_X` | `сустав большого пальца левой руки по оси X` |
| `LEFT_THUMB_Y` | `сустав большого пальца левой руки по оси Y` |
| `RIGHT_THUMB_X` | `сустав большого пальца правой руки по оси X` |
| `RIGHT_THUMB_Y` | `сустав большого пальца правой руки по оси Y` |
| `LEFT_HIP_X` | `левое бедро по оси X` |
| `LEFT_HIP_Y` | `левое бедро по оси Y` |
| `RIGHT_HIP_X` | `правое бедро по оси X` |
| `RIGHT_HIP_Y` | `правое бедро по оси Y` |
| `LEFT_KNEE_X` | `левое колено по оси X` |
| `LEFT_KNEE_Y` | `левое колено по оси Y` |
| `RIGHT_KNEE_X` | `правое колено по оси X` |
| `RIGHT_KNEE_Y` | `правое колено по оси Y` |
| `LEFT_ANKLE_X` | `левая лодыжка по оси X` |
| `LEFT_ANKLE_Y` | `левая лодыжка по оси Y` |
| `RIGHT_ANKLE_X` | `правая лодыжка по оси X` |
| `RIGHT_ANKLE_Y` | `правая лодыжка по оси Y` |
| `LEFT_HEEL_X` | `левая пятка по оси X` |
| `LEFT_HEEL_Y` | `левая пятка по оси Y` |
| `RIGHT_HEEL_X` | `правая пятка по оси X` |
| `RIGHT_HEEL_Y` | `правая пятка по оси Y` |
| `LEFT_FOOT_INDEX_X` | `индекс левой ноги по оси X` |
| `LEFT_FOOT_INDEX_Y` | `индекс левой ноги по оси Y` |
| `RIGHT_FOOT_INDEX_X` | `индекс правой ноги по оси X` |
| `RIGHT_FOOT_INDEX_Y` | `индекс правой ноги по оси Y` |
| `OBJECT_X` | `координата_X` |
| `OBJECT_Y` | `координата_Y` |
| `OBJECT_TRANSPARENCY` | `прозрачность` |
| `OBJECT_BRIGHTNESS` | `яркость` |
| `OBJECT_COLOR` | `цвет` |
| `OBJECT_SIZE` | `размер` |
| `OBJECT_WIDTH` | `ширина` |
| `OBJECT_HEIGHT` | `высота` |
| `WIDTH` | `ширина` |
| `HEIGHT` | `высота` |
| `MOTION_DIRECTION` | `направление_движения` |
| `LOOK_DIRECTION` | `направление_взгляда` |
| `OBJECT_LAYER` | `слой` |
| `OBJECT_DISTANCE_TO` | `расстояние_до_точки_касания` |
| `NXT_SENSOR_1` | `NXT датчик 1` |
| `NXT_SENSOR_2` | `NXT датчик 2` |
| `NXT_SENSOR_3` | `NXT датчик 3` |
| `NXT_SENSOR_4` | `NXT датчик 4` |
| `EV3_SENSOR_1` | `EV3 датчик 1` |
| `EV3_SENSOR_2` | `EV3 датчик 2` |
| `EV3_SENSOR_3` | `EV3 датчик 3` |
| `EV3_SENSOR_4` | `EV3 датчик 4` |
| `PHIRO_FRONT_LEFT` | `передний левый датчик phiro` |
| `PHIRO_FRONT_RIGHT` | `передний правый датчик phiro` |
| `PHIRO_SIDE_LEFT` | `левый боковой датчик phiro` |
| `PHIRO_SIDE_RIGHT` | `правый боковой датчик phiro` |
| `PHIRO_BOTTOM_LEFT` | `левый нижний датчик phiro` |
| `PHIRO_BOTTOM_RIGHT` | `правый нижний датчик phiro` |
| `DRONE_BATTERY_STATUS` | `состояние_батареи_дрона` |
| `DRONE_EMERGENCY_STATE` | `аварийное_состояние_дрона` |
| `DRONE_FLYING` | `дрон_летает` |
| `DRONE_INITIALIZED` | `дрон_инициализирован` |
| `DRONE_USB_ACTIVE` | `USB_дрона_активно` |
| `DRONE_USB_REMAINING_TIME` | `оставшееся_время_USB_дрона` |
| `DRONE_CAMERA_READY` | `камера дрона готова` |
| `DRONE_RECORD_READY` | `дрон готов записывать` |
| `DRONE_RECORDING` | `запись на камеру дрона` |
| `DRONE_NUM_FRAMES` | `количество кадров камеры дрона` |
| `COLLIDES_WITH_EDGE` | `касается_края_экрана` |
| `COLLIDES_WITH_FINGER` | `касается_пальца` |
| `OBJECT_X_VELOCITY` | `скорость_по_оси_X` |
| `OBJECT_Y_VELOCITY` | `скорость_по_оси_Y` |
| `OBJECT_ANGULAR_VELOCITY` | `угловое_ускорение` |
| `LAST_FINGER_INDEX` | `количество_касаний_к_экрану` |
| `FINGER_X` | `касание_к_экрану_по_X` |
| `FINGER_Y` | `касание_к_экрану_по_Y` |
| `FINGER_TOUCHED` | `касается_экрана` |
| `NUMBER_CURRENT_TOUCHES` | `количество_одновременных_касаний` |
| `OBJECT_LOOK_NUMBER` | `номер_образа` |
| `OBJECT_LOOK_WIDTH` | `ширина_образа` |
| `OBJECT_LOOK_HEIGHT` | `высота_образа` |
| `OBJECT_LOOK_NAME` | `название_образа` |
| `OBJECT_NUMBER_OF_LOOKS` | `количество_образов` |
| `OBJECT_BACKGROUND_NUMBER` | `номер_фона` |
| `OBJECT_BACKGROUND_NAME` | `название_фона` |
| `NFC_TAG_ID` | `id_NFC_тега` |
| `NFC_TAG_MESSAGE` | `сообщение_NFC_тега` |
| `GAMEPAD_A_PRESSED` | `на_джойстике_нажато_A` |
| `GAMEPAD_B_PRESSED` | `на_джойстике_нажато_B` |
| `GAMEPAD_UP_PRESSED` | `на джойстике нажато "вверх"` |
| `GAMEPAD_DOWN_PRESSED` | `на джойстике нажато "вниз"` |
| `GAMEPAD_LEFT_PRESSED` | `на джойстике нажато "влево"` |
| `GAMEPAD_RIGHT_PRESSED` | `на джойстике нажато "вправо"` |
| `TEXT_FROM_CAMERA` | `текст с камеры` |
| `TEXT_BLOCKS_NUMBER` | `количество текстовых блоков` |
| `SPEECH_RECOGNITION_LANGUAGE` | `язык прослушивания` |
| `STAGE_WIDTH` | `ширина_экрана` |
| `STAGE_HEIGHT` | `высота_экрана` |
| `MICRO` | `громкость_микрофона` |
| `IP` | `айпи_локального_сервера` |
| `PORT` | `порт_локального_сервера` |
| `FREQ` | `частота_звука` |
| `INTERNET` | `подключен_к_интернету` |
| `BATTARY` | `заряд_батареи` |
| `ARCH` | `архитектура_процессора` |
| `NFC_TECH_LIST` | `NFC_технологии` |
| `NFC_MEMORY_SIZE` | `NFC_размер_памяти` |
| `NFC_IS_WRITABLE` | `NFC_можно_записать` |
| `NFC_TAG_TYPE` | `NFC_тип_метки` |
| `MOUSE_X` | `мышь_X` |
| `MOUSE_Y` | `мышь_Y` |
| `MOUSE_DELTA_X` | `смещение_мыши_X` |
| `MOUSE_DELTA_Y` | `смещение_мыши_Y` |
| `MOUSE_SCROLL` | `прокрутка_мыши` |
| `CLIPBOARD_TEXT` | `текст_буфера_обмена` |
| `KEYBOARD_HEIGHT` | `высота_клавиатуры` |
| `OBJECT_NAME` | `имя_объекта` |

### 6.16. Знаки операторов в редакторе (`strings.xml`)

| `value` в XML | Знак/название в редакторе |
|---|---|
| `LOGICAL_AND` | `и` |
| `LOGICAL_OR` | `или` |
| `LOGICAL_NOT` | `не` |
| `EQUAL` | `=` |
| `NOT_EQUAL` | `≠` |
| `SMALLER_THAN` | `<` |
| `GREATER_THAN` | `>` |
| `SMALLER_OR_EQUAL` | `≤` |
| `GREATER_OR_EQUAL` | `≥` |
| `PLUS` | `+` |
| `MINUS` | `-` |
| `MULT` | `×` |
| `DIVIDE` | `÷` |
| `POW` | `^` |
| `MOD` | — (оператора `MOD` в строках редактора не нашёл; остаток от деления доступен как функция `MOD` — «остаток_от_деления») |
| `STRING_CONCAT` | — (в строках редактора отдельного названия нет) |

## 7. Источники

- Официальный репозиторий: https://github.com/Danveyd/NewCatroid
- Родительский проект/формат: Catrobat (Pocket Code), https://github.com/Catrobat/Catroid
- Пример разобранного файла: `code.xml`, предоставленный пользователем (версия `catrobatLanguageVersion` 1.18, `applicationVersion` 2.2.0)
- Исходный код интерфейса `Brick` (`Brick.java`), предоставленный пользователем — источник каталога `BrickField`/`BrickData`/`Resources` в разделе 6
- Исходный код `BrickInfo.java`, предоставленный пользователем — источник каталога конкретных типов блоков и их локализованных описаний в разделе 6.5
- Исходные файлы `Sensors.java`, `Functions.java`, `Operators.java`, `InternTokenType.java`, `BackwardCompatibleCatrobatLanguageXStream.java`, предоставленные пользователем — источник разделов 6.7–6.12
- Русский `strings.xml` (3761 строка), предоставленный пользователем — источник разделов 6.14–6.16 (локализованные названия функций, датчиков, операторов и примеры параметров)
- Исходный файл `FormulaElement.java`, предоставленный пользователем — источник раздела 6.13 (типы узлов формулы, порядок аргументов, правила вычисления)
- Дерево проекта `project-tree.txt`, предоставленное пользователем — источник списка классов `*Script` в разделе 6.11
- Второй пример `code.xml` ("Отправка мелких медиа"), предоставленный пользователем — источник наблюдений о многоаргументных формулах, списках (`userList`/`USER_LIST`) и индексированных ссылках в разделе 6.6
