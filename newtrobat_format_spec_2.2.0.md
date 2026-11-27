# Формат `.newtrobat` — спецификация для нейросетей

> Проект: **NewCatroid** (форк Pocket Code / Catrobat), https://github.com/Danveyd/NewCatroid
> Файл `.newtrobat`: сохранённый проект блочного визуального программирования (сцены, объекты, скрипты из блоков, формулы, образы, звуки, файлы, библиотеки).
> Описано поведение NewCatroid 2.2.0, язык проекта (`catrobatLanguageVersion`) 1.18.
> Подробные описания всех блоков (назначение, параметры) вынесены в отдельный файл `newtrobat_blocks_reference.md`.

---

## 0. Как пользоваться документом

**Уровни достоверности.** Утверждения основаны на трёх видах источников:
1. **Реальные файлы** `.newtrobat` (раздел 7): структура проверена на настоящих проектах.
2. **Исходный код** NewCatroid (раздел 6): перечни полей, функций, датчиков, правила сериализации и загрузки.
3. **Выводы**: помечены словами «вероятно», «по-видимому», «по названию», «по сообщению пользователя». Их надо считать непроверенными.

**Версии.** Исходники, из которых собран раздел 6, местами новее релиза 2.2.0 (например, поле `elseIfBranches`, которое, по сообщению пользователя, появится в 2.3.0), а официальная wiki местами описывает 2.3.0 (шейдерные экземпляры). Реальные файлы раздела 7 записаны версией 2.2.0.

**Указатель по темам**

| Нужно узнать | Где смотреть |
|---|---|
| состав и структуру архива, расширение, упаковку | 2, 4, 6.24, 6.25, 7.1 |
| скелет и порядок тегов `code.xml` | 0.1, 3, 6.22, 6.28, 6.30 |
| допустимые типы блоков и их имена в XML | 6.5, 6.18, 6.19, 6.28 |
| какие формулы (`category`) и поля есть у блока | 6.20, 6.21, 6.26, справочник блоков |
| вложенные блоки, шапки скриптов, пользовательские блоки | 6.21, 6.32, 7.2 |
| какое событие запускает скрипт («При нажатии» и др.) | 6.11 |
| форматы файлов в `files/` и `libs/` (`.rscene`, `model.bin`, `.newlib`) | 7.2, 7.6, 6.23 |
| формулы: узлы, операторы, функции, датчики | 3.4, 6.7–6.10, 6.13, 6.14–6.16, 6.27 |
| переменные, списки, `DeviceVariables.json` | 3.4, 3.5, 6.26, 6.29, 7.1, 7.2 |
| библиотеки `.newlib`, пользовательские формулы и блоки | 6.23, 7.2–7.5 |
| версии языка, миграции, загрузка и сохранение | 6.12, 6.31, 6.33 |
| 3D-сцены `.rscene` | 7.2 |
| как проверить прочитанное на реальных проектах | 7 |

### 0.1. Краткая сводка формата

**Архив.** ZIP-файл (расширение `.newtrobat`, прежнее `.catrobat` тоже принимается). Все записи это файлы, `code.xml` обычно идёт первым:
```
проект.newtrobat
├── code.xml                       главный файл
├── automatic_screenshot.png       снимок проекта (или manual_screenshot.png); необязателен
├── DeviceVariables.json           значения переменных, записанных на устройство; необязателен
├── DeviceLists.json               то же для списков; необязателен
├── files/                         произвольные файлы проекта (.png, .otf, .obj, .rscene и др.); необязателен
├── libs/                          библиотеки *.newlib и *.jar; необязателен
└── <Имя сцены>/                   по одному каталогу на сцену (имя равно <name> сцены)
    ├── automatic_screenshot.png
    ├── images/   (.nomedia + изображения)
    └── sounds/   (.nomedia + звуки)
```

**Скелет `code.xml`** (порядок тегов зафиксирован):
```xml
<program>
  <header>…теги по алфавиту…</header>
  <settings/>
  <scenes>
    <scene sceneId="UUID">
      <name>…</name>
      <objectList>
        <object type="Sprite" spriteId="UUID" name="…">          <!-- Sprite | GroupSprite | GroupItemSprite -->
          <lookList><look fileName="…" lookId="UUID" name="…"><isWebRequest>false</isWebRequest><valid>true</valid></look></lookList>
          <soundList><sound fileName="…" name="…" soundId="UUID"><midiFile>false</midiFile></sound></soundList>
          <scriptList>
            <script type="StartScript" posX="0.0" posY="0.0">
              <brickList><brick type="…">…</brick></brickList>
              <commentedOut>false</commentedOut>
              <scriptId>UUID</scriptId>
            </script>
          </scriptList>
          <nfcTagList/><userVariables/><userLists/><userDefinedBrickList/>
        </object>
      </objectList>
    </scene>
  </scenes>
  <programVariableList/><programListOfLists/><programMultiplayerVariableList/>
  <disableScientificNotation>false</disableScientificNotation>
</program>
```

**Правила, важные для разбора**
1. Блок: `<brick type="ИмяКласса">` с тегами `brickId`, `commentedOut`, `formulaList`, затем поля базового класса, затем собственные поля блока по алфавиту (6.30). Блок без алиаса записывается элементом с полным именем класса и тем же атрибутом `type` (например, `org.catrobat.catroid.content.bricks.ShowVarFontBrick`, 6.28).
2. Скрипт: `<script type="ИмяКласса" posX posY>`; составные блоки хранят вложенные блоки в полях-списках (`loopBricks`, `ifBranchBricks`, `elseBranchBricks`, `tryBricks` и др., 6.21).
3. Формула: `<formula category="ИМЯ_BrickField">`, внутри поля корневого узла (`additionalChildren`, `leftChild`, `rightChild`, `type`, `value`). Неизвестное имя категории при загрузке вызывает исключение (6.30). Порядок `<formula>` внутри `formulaList` не зафиксирован.
4. Типы узлов формулы: `NUMBER`, `STRING`, `OPERATOR`, `FUNCTION`, `SENSOR`, `USER_VARIABLE`, `USER_LIST`, `USER_DEFINED_BRICK_INPUT`, `BRACKET`, `COLLISION_FORMULA` (6.13). Значение `FUNCTION`, которого нет в `Functions`, это вызов пользовательской формулы из `.newlib` (6.23).
5. Поля со значением `null` в XML не пишутся. Повторяющиеся объекты (переменные, списки, образы, звуки, списки данных пользовательских блоков) записаны один раз, дальше идёт `<тег reference="относительный путь"/>`; индекс `[n]` в пути считается среди одноимённых соседей, начиная с 1 (3.5).
6. Значения переменных и списков не лежат в `code.xml`: там только `name`, `initialIndex` и ключ `deviceValueKey` / `deviceListKey`; значения хранятся в `DeviceVariables.json` / `DeviceLists.json` (6.29).
7. Файл образа это `<сцена>/images/<look/@fileName>`, файл звука это `<сцена>/sounds/<sound/@fileName>`; в формулах файлы из `files/` указаны простыми относительными именами (6.25).
8. Принадлежность объекта к группе определяется порядком в `objectList`: `GroupItemSprite` после `GroupSprite` входят в его группу (6.31).
9. Допустимые версии языка: 0.8 и от 0.9 до 1.18; более новые проекты не загружаются, более старые мигрируют (6.33).
10. Пользовательские блоки и формулы определяются в библиотеках `libs/*.newlib` (`code.txt` на LunoScript, `formulas.xml`, `bricks.xml`), а в `code.xml` есть только ссылки на них (`CustomBrick/definitionId`, значение `FUNCTION`; 6.23).

---

## 1. Общая идея

`.newtrobat` это обычный ZIP-архив (приложение определяет его по окончанию `.zip` или `.newtrobat`, 6.24). Чтобы прочитать проект:

1. Распаковать файл как ZIP.
2. Разобрать `code.xml` (UTF-8): это единственный источник истины о сценах, объектах, скриптах и формулах.
3. Сопоставить имена файлов из `code.xml` с файлами архива: образы и звуки по каталогам сцен, прочие файлы по `files/`.
4. При необходимости загрузить значения переменных из `DeviceVariables.json` и `DeviceLists.json` и определения пользовательских блоков и формул из `libs/*.newlib`.

---

## 2. Структура архива

Подтверждённый состав архива показан в 0.1; реальные примеры в разделе 7.1.

**Правила**
- **`code.xml`** лежит в корне и описывает всю логику проекта, наборы сцен, объектов и ресурсов.
- **Каталоги сцен** названы по имени сцены (`<name>` в `scenes/scene`); спецсимволы в имени кодируются процентной записью (6.33), допустимы пробелы и кириллица (`Fast 2D`, `Меню`). Внутри каталога: `images/`, `sounds/` (в обоих лежит пустой файл `.nomedia`) и `automatic_screenshot.png`.
- **Имена файлов в `images/`** сохраняются «человеческими» (без хеша); при совпадении имён к имени добавляется суффикс `_#0`, `_#1`… перед расширением; для всех образов `look/@fileName` совпадает с именем файла.
- **`files/`** хранит произвольные файлы проекта: подкаталоги допустимы, выход за пределы каталога запрещён (`Project.getFile`, 6.25). Блоки и формулы обращаются к файлам по относительному имени (например, `LoadSceneBrick` со значением `hf.rscene` загружает `files/hf.rscene`).
- **`libs/`** содержит библиотеки `*.newlib` (6.23) и `.jar`-зависимости; при экспорте через `ProjectExportTask` в архив попадает всё содержимое каталога проекта (6.25), в том числе `libs/`, `libs_processed/`, `jniLibs/`, если они есть.
- **Служебные файлы проекта**: `tmp_code.xml` и `undo_code.xml` (временные копии `code.xml`), `permissions.txt` (устарел, удаляется при загрузке проектов старого формата, 6.33). В реальных архивах их не встречалось.
- Сцен может быть любое число (минимум одна): сцены описаны элементами `<scene>` в `<scenes>`.

---

## 3. Формат `code.xml`

`code.xml` — XML-документ в кодировке UTF-8; версия языка записана в `header/catrobatLanguageVersion` (сейчас 1.18). Порядок тегов задаёт сериализатор XStream (6.30); имена элементов задают алиасы классов (6.28).

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
Порядок и имена тегов подтверждены аннотациями `@XStreamAlias` и `@XStreamFieldKeyOrder` у класса `Project` (6.22, 6.30) и реальными файлами (7.1).

### 3.2. `<header>` — метаданные проекта

Теги `<header>` идут **по алфавиту** (по алиасу, если он есть: `screenHeight`, `screenMode`, `screenWidth`). Полная таблица полей с типами и значениями по умолчанию приведена в 6.26. Основные поля:

| Тег | Назначение |
|---|---|
| `applicationName`, `applicationVersion` | приложение, создавшее проект (`NewCatroid`, `2.2.0`; у проекта из Pocket Code `Покет Код`, `1.4.3`) |
| `applicationBuildName/Number/Type` | данные о сборке приложения |
| `catrobatLanguageVersion` | версия языка проекта (1.18); определяет миграции при загрузке (6.33) |
| `programName` | имя проекта; при импорте и копировании заменяется текстовой подстановкой (6.33) |
| `description`, `notesAndCredits`, `tags` | текстовые метаданные |
| `deviceName`, `platform`, `platformVersion` | устройство и ОС (`Android`, API `36`) |
| `screenWidth`, `screenHeight`, `screenMode` | размер экрана и режим масштабирования (`STRETCH` и др.) |
| `landscapeMode`, `customResolution`, `scenesEnabled`, `isCastProject` | флаги проекта |
| `physicsWidthArea`, `physicsHeightArea` | размеры физического мира |
| `programLicense`, `mediaLicense` | лицензии |
| `remixOf`, `gitRemoteUrl`, `url`, `userHandle` | ссылки и автор |
| `dateTimeUpload`, `listeningLanguageTag` | дата выгрузки на сервер, язык распознавания речи |

Заголовок не обновляется при каждом сохранении: у проекта, импортированного из Pocket Code и дополненного блоками NewCatroid, остались значения Pocket Code (7.5). Большинство текстовых полей могут быть пустыми.

### 3.3. `<settings>`

Список настроек проекта. Пустой (`<settings/>`) или содержит настройки LEGO:
```xml
<settings>
  <setting type="LegoNXTSetting">
    <portSensorMapping>
      <nxtPort><number>0</number><sensor>NO_SENSOR</sensor></nxtPort>
      …
    </portSensorMapping>
  </setting>
</settings>
```
Типы настроек: `LegoNXTSetting`, `LegoEV3Setting` (6.31, 7.3).

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
- `sceneId` (атрибут, UUID) и `<name>` идентифицируют сцену; имя совпадает с именем каталога сцены (с учётом кодирования, 6.33).
- Объектов может быть любое число. Порядок тегов внутри `<object>` как в примере (6.22).

#### Объект (`<object>`)

| Атрибут/тег | Назначение |
|---|---|
| `type` | `Sprite`, `GroupSprite` или `GroupItemSprite`; принадлежность к группе по порядку в `objectList` (6.31) |
| `spriteId`, `name` | UUID и имя объекта (атрибуты) |
| `lookList` | образы объекта; каждый `<look>` ссылается на файл в `<сцена>/images/` |
| `soundList` | звуки; каждый `<sound>` ссылается на файл в `<сцена>/sounds/` |
| `scriptList` | скрипты объекта |
| `nfcTagList` | NFC-метки (`<nfcTag>` с `name`, `uid`) |
| `userVariables`, `userLists` | локальные переменные и списки объекта |
| `userDefinedBrickList` | определения пользовательских блоков (6.32) |

#### `<look>` и `<sound>`

```xml
<look fileName="Фон.png" lookId="UUID" name="Фон">
  <isWebRequest>false</isWebRequest>
  <valid>true</valid>
</look>
<sound fileName="click.wav" name="click" soundId="UUID">
  <midiFile>false</midiFile>
</sound>
```
- `fileName` — имя файла в `<сцена>/images/` или `<сцена>/sounds/`; `name` от имени файла не зависит; имя образа внутри объекта уникализируется суффиксом (`gh`, `gh (1)`).
- `isWebRequest`, `valid`, `midiFile` — флаги; `midiFile` не вычисляется по расширению (7.4).
- Блоки хранят выбранный образ или звук ссылкой: `<look reference="../../../../../lookList/look[2]"/>`.

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
- `type` — класс скрипта: `StartScript`, `WhenScript`, `WhenTouchDownScript`, `BroadcastScript`, `WhenConditionScript`, `UserDefinedScript` и другие (полный перечень и поля в 6.11, 6.21, 6.26, 6.28).
- `posX`, `posY` — положение на холсте редактора, на выполнение не влияют.
- `brickList` — блоки, выполняемые сверху вниз; вложенные блоки составных блоков лежат в полях-списках самих блоков (6.21).

#### `<brick>` — программный блок

```xml
<brick type="SetVariableBrick">
  <brickId>UUID</brickId>
  <commentedOut>false</commentedOut>
  <formulaList>...</formulaList>
  <userVariable .../>
</brick>
```
- `type` — имя класса блока (допустимые значения: 6.5, 6.18); блок без алиаса записывается элементом с полным именем класса, `type` при этом тоже есть (6.28).
- `brickId` — UUID блока, `commentedOut` — блок отключён, но сохранён.
- `formulaList` — формулы параметров; допустимые `category` каждого блока перечислены в 6.20. Блоки без формульных параметров тега `formulaList` не имеют.
- Остальные теги — поля блока (выбранный пункт списка, ссылка на образ, звук, переменную, вложенные блоки и т. д., 6.21).

#### `<formula>` — выражения

```xml
<formula category="VARIABLE">
  <additionalChildren/>
  <leftChild> … </leftChild>
  <rightChild> … </rightChild>
  <type>OPERATOR</type>
  <value>LOGICAL_OR</value>
</formula>
```
- Формула это дерево узлов: каждый узел имеет `type`, `value`, при необходимости `leftChild`, `rightChild` и `additionalChildren` (лишние аргументы функций, 6.6, 6.27).
- `category` — одно из значений `BrickField` (6.1); для пользовательских блоков вместо `category` пишется `input="имя входа"` (6.32).
- Типы узлов (`type`): `NUMBER`, `STRING`, `OPERATOR` (6.9), `FUNCTION` (6.8, 6.27), `SENSOR` (6.7), `USER_VARIABLE`, `USER_LIST`, `USER_DEFINED_BRICK_INPUT`, `BRACKET`, `COLLISION_FORMULA` (6.13).

#### Переменные и списки внутри блока

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

<userList>
  <deviceListKey>UUID</deviceListKey>
  <initialIndex>0</initialIndex>
  <name>имя списка</name>
</userList>
```
Это определение; повторные упоминания тех же переменной или списка записываются ссылкой `reference` (3.5). Значения лежат в `DeviceVariables.json` и `DeviceLists.json` (6.29).

### 3.5. `<programVariableList>`

```xml
<programVariableList>
  <userVariable reference="../../scenes/scene/objectList/object/scriptList/script/brickList/brick/userVariable"/>
</programVariableList>
```
Глобальные переменные проекта записаны ссылками (`reference`, механизм XStream) на первое определение в дереве `<scenes>`: относительный путь, где `..` означает родительский элемент, а `[n]` номер среди одноимённых соседей, начиная с 1 (например, `object[2]`, `brick[3]`). Тем же способом записаны `programListOfLists`, `programMultiplayerVariableList`, образы и звуки в блоках и общие списки данных пользовательских блоков.

### 3.6. `<programListOfLists>`

Глобальные списки проекта; структура как у `<programVariableList>`, только с `<userList>` (6.6).

### 3.7. `<programMultiplayerVariableList>`

Переменные многопользовательского режима; записаны ссылками, как `<programVariableList>` (7.3).

### 3.8. `<disableScientificNotation>`

Булев флаг: отключать ли научную запись чисел при выводе.

---

## 4. Связь XML и файлов архива

| Ссылка в `code.xml` | Где искать файл |
|---|---|
| `scene/name` | каталог `<Имя сцены>/` в корне архива |
| `look/@fileName` у объекта сцены `S` | `<S>/images/<fileName>` |
| `sound/@fileName` у объекта сцены `S` | `<S>/sounds/<fileName>` |
| строка-имя файла в формуле или параметре блока (например, `Blogger Sans-Bold.otf`, `hf.rscene`) | `files/<имя>` (допустимы подкаталоги) |
| `CustomBrick/definitionId`, значение `FUNCTION`, которого нет в `Functions` | определение в `libs/*.newlib` (`bricks.xml`, `formulas.xml`) |
| `deviceValueKey`, `deviceListKey` | ключ в `DeviceVariables.json`, `DeviceLists.json` |

---

## 5. Практические рекомендации для нейросети при разборе `.newtrobat`

1. **Распаковать ZIP** и прочитать `code.xml` XML-парсером в UTF-8. Имена элементов могут содержать точки (`org.catrobat.catroid.content.bricks.ShowVarFontBrick`): использовать парсер, который принимает такие имена.
2. **Блок определять по атрибуту `type`**, а не по имени элемента. Допустимые значения `type` перечислены в 6.18; для набора формул и полей блока использовать 6.20 и 6.21.
3. **Не опираться на порядок `<formula>` внутри `formulaList`**: он определяется хеш-картой. Порядок остальных тегов фиксирован (6.30).
4. **Разрешать ссылки `reference`** относительно родителя элемента; индекс `[n]` считается с 1 среди одноимённых соседей. Для переменных и списков использовать определение по ссылке.
5. **Отсутствие тега означает `null`** или значение по умолчанию (например, `objectToClone` у `CloneBrick`, `nfcTag` у `WhenNfcScript`, `elseIfBranches` у «если»).
6. **Проверять `category`**: значение, не входящее в `BrickField` (6.1), вызывает ошибку загрузки в самом приложении. Неизвестный `type` блока приложение только логирует, а что дальше происходит с таким блоком, по исходникам не определено (6.19).
7. **Формулы разбирать рекурсивно** по `leftChild`, `rightChild`, `additionalChildren`; порядок аргументов функций описан в 6.27.
8. **Файлы** сопоставлять по таблице раздела 4; имена в `files/` указываются простыми относительными строками.
9. **Значения переменных** брать из `DeviceVariables.json` и `DeviceLists.json` по `deviceValueKey` и `deviceListKey`; в `code.xml` их нет.
10. **Версию языка проверять в `header/catrobatLanguageVersion`**: приложение принимает 0.8 и от 0.9 до 1.18 (6.33). Формат продолжает развиваться (3D, Fast2D, PockeTensor, библиотеки, пользовательские блоки), поэтому список типов блоков, функций и датчиков надо считать открытым и проверять по актуальным перечням раздела 6.

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

### 6.5. Каталог конкретных типов блоков (`Brick`, из `BrickInfo.java`)

`BrickInfo.java` — локализованный справочник NewCatroid: словарь `Class<? extends Brick> → строка описания` (отдельно для ru/en/pt/zh). Это даёт "человеческую" расшифровку значения `brick type="..."` в `code.xml`: имя класса совпадает с значением атрибута `type` за вычетом суффикса `.class` (например, `add(MoveNStepsBrick.class, ...)` → в XML это `<brick type="MoveNStepsBrick">`).

Ниже — перечень типов, описанных в `BrickInfo.java` (393 уникальных, версия NewCatroid 2.2.0+), сгруппированный тематически. Он **не полный**: в каталоге `content/bricks` классов больше, недостающие блоки перечислены в 6.18. Каждое имя — валидное значение `brick/@type`. Точные формулировки описаний на русском содержатся в исходнике `BrickInfo.java` (`initRussianDescriptions()`), здесь при необходимости даны только пояснения к неочевидным группам.

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

В `code.xml` это узел `<type>FUNCTION</type><value>ИМЯ</value>`. Допустимые значения — константы enum `Functions` (около 230). Аргументы лежат в `leftChild`, `rightChild` и далее в `additionalChildren` (см. 6.6). Что делает каждая функция и в каком порядке принимает аргументы, описано в 6.27.

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
| PockeTensor (тензоры и ИИ-модели; префикс `PT_`) | `PT_ARGMAX`, `PT_VALUE`, `PT_VALUEND`, `PT_SHAPE`, `PT_DUMP`, `PT_TOTALSIZE`, `PT_SAMPLE` |
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

Это перечень по именам файлов, содержимое классов я не видел, поэтому поля конкретных скриптов (например, `spriteToBounceOffName` у `WhenBounceOffScript`) здесь не описаны. Какой блок-шапка хранит какой скрипт, показано в 6.21; какие классы получают алиас `script`, а какие нет, в 6.28; простые поля скриптов (например, `receivedMessage` у `BroadcastScript`) приведены в 6.26.

**Какое событие запускает скрипт (названия в редакторе и смысл).** Подписи взяты из `strings.xml`, смысл из `BrickInfo.java`, а для первых двух строк это подтверждено ещё и пользователем:

| Блок-шапка → скрипт | Подпись в редакторе | Когда запускается |
|---|---|---|
| `WhenBrick` → `WhenScript` | «При нажатии» | при нажатии пальца **на спрайт** (на сам объект, которому принадлежит скрипт) |
| `WhenTouchDownBrick` → `WhenTouchDownScript` | «При нажатии на экран» | когда палец касается **экрана** (в любом месте) |
| `WhenSpriteReleasedBrick` → `WhenSpriteReleasedScript` | | когда палец отпускает спрайт |
| `WhenFingerMovedOverSpriteBrick` → `WhenFingerMovedOverSpriteScript` | | постоянно, пока палец движется по спрайту |

На странице официальной wiki (`when` и `when_touch_down`) эти два блока описаны наоборот (будто «При нажатии» реагирует на любое касание экрана, а «При нажатии на экран» на нажатие конкретного персонажа); это ошибка текста wiki, в справочнике блоков она исправлена.

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
- Значение `FUNCTION`, которого нет в `Functions`, ищется среди **пользовательских формул** (`CustomFormulaManager`, они пишутся на LunoScript) по уникальному имени. Такие формулы определяются в `formulas.xml` внутри библиотек `.newlib` (6.23); их `<value>` равен атрибуту `id`. Аргументы передаются в том же порядке: `leftChild`, `rightChild`, затем `additionalChildren`. Если такой формулы нет, результат `0`; если определение есть, но его библиотека не загружена, результат строка `LIB NOT FOUND`, а если в библиотеке нет нужной функции, строка `FUNC NOT FOUND` (6.27).
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

### 6.17. Категории палитры и официальная wiki (`newcatroid.mindpy.dev/docs`)

Из сохранённой страницы документации («Введение») можно взять только общую структуру: страницы отдельных блоков в файл не попали. Тем не менее это единственный источник, показывающий **реальные категории палитры** редактора.

**Категории палитры блоков (порядок как в боковом меню wiki)**
События, Управление, Движение, Звук, Внешний вид, Перо, Данные, Устройство, Lego NXT, Lego EV3, Arduino, Дрон, Raspberry Pi, Chromecast, Вышивка, Графики, Нейросети, Pocketensor, Fast2D, Файл, 3D, Интернет, Утверждения.

Как это сочетается с остальными разделами спецификации:
- Категории «Дрон», «Lego NXT», «Lego EV3», «Arduino», «Raspberry Pi», «Вышивка», «Chromecast» совпадают с группами полей `BrickField` и ресурсов `Resources` (6.1, 6.3).
- Категория «Утверждения» соответствует блокам и полям `ASSERT_*` (6.1, 6.2): это тестовые проверки внутри проекта.
- «Pocketensor» это тензорная библиотека; ей принадлежат функции `PT_*` (6.8), а в `strings.xml` её описание: «Добавляет работу с тензорами и позволяет создавать ИИ модели».
- «Fast2D» соответствует функциям `F2D_*` (6.8).
- «Нейросети» (ИИ-блоки: Gemini, GPT, загрузка и предсказание нейросети) по составу в 6.5 разбиты по темам «ИИ / нейросети»; соответствие отдельных блоков категории «Нейросети» в этой странице не показано.
- Для категорий «Графики», «Данные», «Файл» и «Интернет» точный состав блоков в присланном файле не указан; соответствие с группами из 6.5 (файлы, сеть и т. д.) логичное, но без списка блоков я его не подтверждаю.

**Основные понятия из документации**
- **Проект** — совокупность сцен, переменных, списков и ресурсов.
- **Сцена** — отдельный экран или уровень проекта.
- **Объект (спрайт)** — сущность на сцене с позицией, размером, образами и скриптами.
- **Скрипт** — последовательность блоков, начинающаяся с блока-шапки (события).
- **Переменная / список** — именованные контейнеры данных.
- **Клон** — копия объекта, создаваемая во время выполнения.

Это совпадает с XML: проект это `<program>`, сцена `<scene>`, объект `<object type="Sprite">`, скрипт `<script>`, переменные и списки `userVariable` и `userList`. Клонов в `code.xml` как отдельной сущности нет: они создаются в процессе работы через блоки `CloneBrick`, `CloneAndNameBrick`.

**Что ещё сказано о платформе.** NewCatroid позиционируется как открытая платформа визуального программирования с поддержкой 3D, ИИ, Python, сети, Git и собственного языка **LunoScript** (в `Functions.java` для него есть пометка `@LunoClass`, в 6.5 блоки `LunoScriptBrick`, `RunLuaBrick`, `RunPythonScriptBrick`). Лицензия проекта — AGPL v3.

**Структура самой wiki.** Каждый раздел левого меню это отдельная страница со списком блоков категории; на странице блока, по описанию из введения, есть логика выполнения, параметры, примеры и пограничные случаи. Блоки в wiki рисуются как SVG (`nc-block-wrap`), а если блок не найден, показывается заглушка `nc-block-missing`. Для документации формата `.newtrobat` содержимое этих страниц ценно как описание **поведения** блоков: оно отвечает на вопрос «что делает блок», на который `BrickInfo.java` отвечает одной строкой.

### 6.18. Полный перечень классов блоков (`content/bricks`) и сверка с `BrickInfo.java`

Дерево проекта показывает каталог `catroid/src/main/java/org/catrobat/catroid/content/bricks`: в нём **658 файлов** (по одному классу на файл). Список из 6.5 (393 типа) не полный: `BrickInfo.java` описывает не все блоки. Сопоставление страниц официальной wiki (617 блоков) с этим каталогом по правилу «`snake_case` id → `CamelCase` + `Brick`» дало такой результат:

| Результат | Количество |
|---|---|
| Страница wiki нашла класс в каталоге | 606 из 617 |
| из них блоки, которых нет в `BrickInfo.java` (то есть нет в 6.5) | 217 |
| Страницы без найденного класса (все в разделе «Внешний вид»: шейдеры и эффекты) | 11 |

Имя файла даёт имя класса, а значение `<brick type="...">` в XML равно простому имени класса (это подтверждает `XStreamBrickConverter`, см. 6.19). Для 39 файлов на Kotlin (из 658) имя класса обычно совпадает с именем файла, но по дереву проверить это нельзя.

**Блоки из `content/bricks`, которых нет в 6.5, но у которых есть страница wiki** (сгруппированы по разделу wiki)

**События** (7): `BroadcastWithParamsBrick`, `BroadcastWithParamsReceiverBrick`, `LockMouseBrick`, `UnlockMouseBrick`, `WhenMouseButtonClickedBrick`, `WhenMouseWheelScrolledBrick`, `WhenNfcBrick`

**Управление** (8): `ExitStageBrick`, `IfLogicBeginBrick`, `OpenUrlBrick`, `PhiroIfLogicBeginBrick`, `SetNfcTagBrick`, `TapAtBrick`, `TapForBrick`, `TouchAndSlideBrick`

**Движение** (4): `PhiroMotorMoveBackwardBrick`, `PhiroMotorMoveForwardBrick`, `PhiroMotorStopBrick`, `SetBounceBrick`

**Звук** (9): `ChangeTempoByNBrick`, `ListenMicroBrick`, `PauseForBeatsBrick`, `PhiroPlayToneBrick`, `PlayDrumForBeatsBrick`, `PlayNoteForBeatsBrick`, `SetInstrumentBrick`, `SetListeningLanguageBrick`, `SetTempoBrick`

**Внешний вид** (9): `BackgroundRequestBrick`, `ParticleEffectAdditivityBrick`, `PhiroRGBLightBrick`, `SayBubbleBrick`, `SayForBubbleBrick`, `ShowTextBrick`, `ShowTextColorSizeAlignmentBrick`, `ThinkBubbleBrick`, `ThinkForBubbleBrick`

**Перо** (6): `ClearBackgroundBrick`, `PenDownBrick`, `PenUpBrick`, `SetPenColorBrick`, `SetPenSizeBrick`, `StampBrick`

**Данные** (22): `AddItemToUserListBrick`, `ChangeVariableBrick`, `ClearUserListBrick`, `DeleteAllTablesBrick`, `DeleteItemOfUserListBrick`, `DeleteTableBrick`, `DeleteVarBrick`, `DeleteVarsBrick`, `HideText3Brick`, `HideTextBrick`, `InsertItemIntoUserListBrick`, `InsertTableBrick`, `ReadListFromDeviceBrick`, `ReplaceItemInUserListBrick`, `SetVariableBrick`, `SetVariableEasingBrick`, `ShowText3Brick`, `ShowTextFontBrick`, `ShowTextRotationBrick`, `ShowVarFontBrick`, `StringToTableBrick`, `WriteListOnDeviceBrick`

**Устройство** (7): `HideStatusBarBrick`, `OpenFilesBrick`, `PauseVideoBrick`, `PlayVideoBrick`, `ResetTimerBrick`, `SeekVideoBrick`, `SetViewPositionBrick`

**Lego NXT** (4): `LegoNxtMotorMoveBrick`, `LegoNxtMotorStopBrick`, `LegoNxtMotorTurnAngleBrick`, `LegoNxtPlayToneBrick`

**Lego EV3** (5): `LegoEv3MotorMoveBrick`, `LegoEv3MotorStopBrick`, `LegoEv3MotorTurnAngleBrick`, `LegoEv3PlayToneBrick`, `LegoEv3SetLedBrick`

**Arduino** (2): `ArduinoSendDigitalValueBrick`, `ArduinoSendPWMValueBrick`

**Дрон** (13): `DroneEmergencyBrick`, `DroneFlipBrick`, `DroneMoveBackwardBrick`, `DroneMoveDownBrick`, `DroneMoveForwardBrick`, `DroneMoveLeftBrick`, `DroneMoveRightBrick`, `DroneMoveUpBrick`, `DronePlayLedAnimationBrick`, `DroneSwitchCameraBrick`, `DroneTakeOffLandBrick`, `DroneTurnLeftBrick`, `DroneTurnRightBrick`

**Raspberry Pi** (4): `RaspiIfLogicBeginBrick`, `RaspiPwmBrick`, `RaspiSendDigitalValueBrick`, `WhenRaspiPinChangedBrick`

**Chromecast** (1): `WhenGamepadButtonBrick`

**Вышивка** (8): `RunningStitchBrick`, `SetThreadColorBrick`, `SewUpBrick`, `StitchBrick`, `StopRunningStitchBrick`, `TripleStitchBrick`, `WriteEmbroideryToFileBrick`, `ZigZagStitchBrick`

**Графики** (14): `JumpingSumoAnimationsBrick`, `JumpingSumoJumpHighBrick`, `JumpingSumoJumpLongBrick`, `JumpingSumoMoveBackwardBrick`, `JumpingSumoMoveForwardBrick`, `JumpingSumoNoSoundBrick`, `JumpingSumoRotateLeftBrick`, `JumpingSumoRotateRightBrick`, `JumpingSumoSoundBrick`, `JumpingSumoTakingPictureBrick`, `JumpingSumoTurnBrick`, `SavePlotBrick`, `StartPlotBrick`, `StopPlotBrick`

**Нейросети** (1): `SetDnsBrick`

**Pocketensor** (24): `MLLoadBrick`, `MLSaveBrick`, `MLStepAdamBrick`, `MLStepAdamWBrick`, `PtAttentionBrick`, `PtBackwardBrick`, `PtClipGradBrick`, `PtConv2DBrick`, `PtCreateNormalTensorBrick`, `PtCreateTensorBrick`, `PtDropoutBrick`, `PtEmbeddingBrick`, `PtGruCellBrick`, `PtLayerLinearBrick`, `PtLstmCellBrick`, `PtMaxPool2DBrick`, `PtOpBrick`, `PtReshapeBrick`, `PtSetByIndexBrick`, `PtSetTensorBrick`, `PtSetTrainingBrick`, `PtSliceBrick`, `PtStepBrick`, `PtZeroGradBrick`

**Fast2D** (16): `Fast2DApplyForceBrick`, `Fast2DApplyImpulseBrick`, `Fast2DCreateBrick`, `Fast2DDeleteBrick`, `Fast2DMakePhysicsBrick`, `Fast2DSetAngularVelocityBrick`, `Fast2DSetCameraBrick`, `Fast2DSetCollisionFilterBrick`, `Fast2DSetColorBrick`, `Fast2DSetGravityBrick`, `Fast2DSetPhysicsVelocityBrick`, `Fast2DSetPositionBrick`, `Fast2DSetRotationBrick`, `Fast2DSetScaleBrick`, `Fast2DSetTextureBrick`, `Fast2DSetVelocityBrick`

**Файл** (6): `AddFileToApkBrick`, `DeleteFromApkBrick`, `ExtractFileBrick`, `GenerateKeyBrick`, `SignApkBrick`, `UpdateManifestBrick`

**3D** (44): `Apply3dForceBrick`, `CameraLookAtBrick`, `CastRayBrick`, `CreateSpringConstraintBrick`, `KeyframeAnimationBrick`, `ObjectLookAtBrick`, `ObjectLookAtCorrectBrick`, `RemovePbrLightBrick`, `Set3dGravityBrick`, `Set3dPositionBrick`, `Set3dRotationBrick`, `Set3dVelocityBrick`, `SetAmbientLightBrick`, `SetAnimationSpeedBrick`, `SetBackgroundLightBrick`, `SetCameraPositionBrick`, `SetCameraRangeBrick`, `SetCameraRotationBrick`, `SetDirectionalLight2Brick`, `SetEmissiveBrick`, `SetFogBrick`, `SetParticleEmissionBrick`, `SetRotationLockBrick`, `SetShaderUniformFloatBrick`, `SetShaderUniformVec3Brick`, `SetSkyColorBrick`, `SetSkyboxBrick`, `SetSoundInstancePitchBrick`, `SetSoundInstanceVolumeBrick`, `SetSpawnInvisibleBrick`, `SetTextureTilingBrick`, `StopAnimationBrick`, `ThreedAlignNormalBrick`, `ThreedAttachObjectToBoneBrick`, `ThreedBindBoneToObjectBrick`, `ThreedCreateCylinderBrick`, `ThreedCreateFixedConstraintBrick`, `VoxelBuildBrick`, `VoxelConfigBrick`, `VoxelCreateWorldBrick`, `VoxelDeleteBrick`, `VoxelLoadStringBrick`, `VoxelSetBlockBrick`, `VoxelSetTransparentBrick`

**Утверждения** (3): `AssertEqualsBrick`, `AssertUserListsBrick`, `ParameterizedBrick`

**Блоки из `content/bricks` без страницы в wiki и без записи в `BrickInfo.java`** (17): `ApplyShaderBrick`, `BroadcastMessageBrick`, `CreateParticleEffectBrick`, `EmitParticleBurstBrick`, `Fast2DSetZIndexBrick`, `ReportBrick`, `SetParticleBufferRenderBrick`, `SetParticlePropertyBrick`, `SetParticleTransformBrick`, `SetShadowsBrick`, `SetTextBrick`, `ShaderBrick`, `SpawnParticleInstanceBrick`, `StopParticleInstanceBrick`, `UpdateScreenBrick`, `UserDefinedBrick`, `UserDefinedReceiverBrick`. Это тоже существующие классы; назначение по присланным материалам неизвестно, судить можно только по имени.

**Служебные классы** (по именам, вероятно, базовые, вспомогательные или парные «закрывающие» части составных блоков, а не отдельные блоки палитры): `Brick`, `CompositeBrick`, `CustomBrick`, `ElseIfSeparatorBrick`, `EmptyEventBrick`, `EndBrick`, `FormulaBrick`, `IfLogicElseBrick`, `IfLogicEndBrick`, `IfThenLogicEndBrick`, `ListSelectorBrick`, `LoopEndBrick`, `LoopEndlessBrick`, `NativeLayerBrick`, `NoneBrick`, `ParameterizedEndBrick`, `ScriptBrick`, `SubCategoryHeaderBrick`, `TestBrick`, `UnknownBrick`, `UserDataBrick`, `UserListBrick`, `UserVariableBrick`, `VisualPlacementBrick`. Рядом в каталоге лежат ещё вспомогательные типы без суффикса `Brick`: `BrickBaseType`, `ScriptBrickBaseType`, `ConcurrentFormulaHashMap`, `UserDataHashMap`, `ElseIfBranch`, `UserVariableBrickInterface`, `UserVariableBrickWithFormula`, `UserVariableBrickWithVisualPlacement`, а также подкаталог `brickspinner`. Различить абстрактные и конкретные классы по дереву нельзя.

**Блоки с вариантами на «2»**: `PrepareSoundBrick2` и `StopSoundBrick2` лежат в каталоге и описаны в `BrickInfo.java`, но страниц wiki у них нет; `IfLogicElseBrick` и `IfThenLogicEndBrick` описаны в `BrickInfo.java` и, судя по именам, являются частями составных блоков «если».

**Страницы шейдеров и эффектов без найденного класса** (`apply_effect`, `remove_effect`, `set_effect_intensity`, `clear_effects`, `create_shader_instance`, `apply_shader_instance`, `set_shader_instance_uniform`, `detach_shader_instance`, `remove_shader_instance`, `exclude_sprite_from_shader`, `include_sprite_to_shader`). Классов с такими именами в каталоге нет. Присланные исходники двух близких классов уточняют картину:

| Класс | Поля формул (`BrickField`) | Прочие поля | Что видно |
|---|---|---|---|
| `ApplyShaderBrick` | `NAME` (идентификатор эффекта), `TEXT` (цель), `VALUE_1` (сила) | `presetSelection` (целое, выбор пресета из выпадающего списка `brick_shader_presets`) | По набору параметров (эффект, цель, выпадающий список) похож на страницу `apply_effect`. Но в wiki у `apply_effect` нет параметра силы, и там три параметра вместо четырёх; кроме того, страница относится к версии 2.3.0, а `ApplyShaderBrick` есть в коде 2.2.0, поэтому это может быть более ранняя версия блока или другой блок. Соответствие вероятное, но не доказанное |
| `ShaderBrick` | `VERTEX` (код вершинного шейдера), `FRAGMENT` (код фрагментного шейдера) | нет | Это блок «задать шейдер кодом»; ни одной из 11 страниц выше он не соответствует (те описывают именованные экземпляры и эффекты). Отдельной страницы wiki у него нет |

Остальные 10 страниц (`remove_effect`, `set_effect_intensity`, `clear_effects` и все `*_shader_instance`) ни с одним классом не сопоставлены. Классы `SetShaderUniformFloatBrick` и `SetShaderUniformVec3Brick`, которые по имени могли бы подойти, уже соответствуют своим страницам `set_shader_uniform_float` и `set_shader_uniform_vec3` (раздел «3D») и не подходят к `set_shader_instance_uniform`: у них нет параметра «Экземпляр». Классов, связанных с именованными экземплярами шейдеров или с удалением эффектов, в каталоге нет вообще. По сообщению пользователя, эти страницы относятся к версии NewCatroid 2.3.0, а присланный код соответствует актуальной версии 2.2.0 (вышла 21 июля), поэтому блоков с такими именами в коде нет. Это сообщение по файлам не проверялось.

Подробные описания и параметры блоков из wiki собраны в отдельном файле `newtrobat_blocks_reference.md`.

### 6.19. Как блок записывается в XML (`XStreamBrickConverter.java`, `ApplyShaderBrick.java`, `ShaderBrick.java`)

**Атрибут `type`.** Конвертер при записи добавляет к каждому блоку атрибут `type` со значением `source.getClass().getSimpleName()`, то есть **простое имя класса без пакета**: `<brick type="ApplyShaderBrick">`. Регистр важен, пространства имён нет. Остальные поля блока записываются стандартным `ReflectionConverter` XStream: каждое поле класса становится тегом внутри `<brick>`.

**Как блок читается.** Для значения `type` конвертер пробует загрузить класс `<пакет>.<type>` по очереди в двух пакетах: `org.catrobat.catroid.content.bricks` и `org.catrobat.catroid.physics.content.bricks`. В присланном дереве второго пакета с блоками нет (в `physics/content` лежит только `ActionPhysicsFactory.kt`), так что фактически все блоки находятся в первом. Если класс не найден, в лог пишется сообщение `Brick <type> not found in packages`, а дальше разбор идёт стандартным механизмом. Что именно произойдёт с таким блоком после этого, по самому файлу сказать нельзя; надёжнее считать, что блок с неизвестным `type` не загрузится.

Вывод для разбора `code.xml`: допустимые значения `brick/@type` это имена классов из каталога `content/bricks` (раздел 6.18); значения из `BrickInfo.java` (6.5) лишь их часть.

**Как блок объявляет свои формулы.** Блоки с формулами наследуют `FormulaBrick`. В конструкторе класс вызывает `addAllowedBrickField(BrickField.X, R.id.…)` для каждого параметра, и это определяет, какие значения `formula/@category` допустимы у этого блока. Например:
- `ApplyShaderBrick`: `NAME`, `TEXT`, `VALUE_1`;
- `ShaderBrick`: `VERTEX`, `FRAGMENT`.
- `SetShaderUniformFloatBrick`: `THREED_UNIFORM_NAME`, `VALUE_X`;
- `SetShaderUniformVec3Brick`: `THREED_UNIFORM_NAME`, `VALUE_X`, `VALUE_Y`, `VALUE_Z`.

Таблицы параметров в официальной wiki при этом неполны: у страницы `set_shader_uniform_vec3` указан один параметр (имя), хотя у класса четыре формулы. Поэтому по wiki нельзя судить, какие именно `category` есть у блока; надёжный источник — конструктор класса. По той же причине отсутствие параметра «сила» у страницы `apply_effect` не противоречит её соответствию `ApplyShaderBrick`.

Конструкторы с `String`/`double` создают формулу-константу из значения (`new Formula("blur")`), с `Formula` принимают готовое дерево (6.13). Поэтому, чтобы узнать, какие поля формул у конкретного блока, нужно смотреть его конструктор; готовая таблица «блок → поля» для всего каталога приведена в 6.20.

**Нестандартные поля блока.** Поля, не являющиеся формулами, пишутся отдельными тегами. У `ApplyShaderBrick` это `presetSelection` (индекс выбранного пункта списка). Ожидаемый вид по правилам рефлексии (в реальном `code.xml` такой блок не встречался, структура выведена из кода):
```xml
<brick type="ApplyShaderBrick">
  <brickId>UUID</brickId>
  <commentedOut>false</commentedOut>
  <formulaList>
    <formula category="NAME">…</formula>
    <formula category="TEXT">…</formula>
    <formula category="VALUE_1">…</formula>
  </formulaList>
  <presetSelection>0</presetSelection>
</brick>
```
Порядок тегов: если у класса есть `@XStreamFieldKeyOrder`, он задан списком (только `Project`, `Scene`, `Sprite`, `LanguageObject`); иначе поля сортируются по глубине класса и затем по алфавиту (6.30), то есть у блока сначала `brickId`, `commentedOut`, потом `formulaList`, потом поля самого блока. Для чтения XML порядок тегов, как правило, не важен, потому что XStream сопоставляет теги с полями по имени (это общее свойство XStream).

**Что добавляет базовый класс `FormulaBrick` (`FormulaBrick.java`).** Почти все блоки с параметрами наследуют этот абстрактный класс (сам он значением `type` быть не может).
- Поле `formulaMap` помечено `@XStreamAlias("formulaList")`: именно оно записывается как тег `<formulaList>`. Тип поля `ConcurrentFormulaHashMap` (ключ — `FormulaField`, значение — `Formula`); как карта превращается в элементы `<formula category="…">`, решает конвертер `XStreamConcurrentFormulaHashMapConverter` (в дереве есть, исходник я не видел).
- `FormulaField` — интерфейс, а `BrickField` лишь одна из его реализаций (метод `getAllFormulaFieldsWithFormulas` отдельно отфильтровывает ключи, которые являются `BrickField`). Значит, ключи бывают и других типов: класс `InputFormulaField` пользовательских блоков тоже реализует `Brick.FormulaField` (см. 6.26).
- `addAllowedBrickField` кладёт в карту формулу-число `0` по умолчанию: пока параметр не задан, у него значение `0`.
- Обращение к категории, которой нет у блока, бросает `IllegalArgumentException` с текстом `Incompatible Brick Field: <Класс> does not have BrickField.<ИМЯ>` (при чтении и при записи значения). Как загрузчик XML ведёт себя с лишней `category`, по этому файлу не определить.
- Поле `brickFieldToTextViewIdMap` помечено `transient`: связь «параметр → элемент интерфейса» в XML не попадает.
- Метод `replaceFormulaBrickField(старая, новая)` переносит формулу под новую категорию: так переименовывают параметры при миграции проектов.
- Если запросить отсутствующую формулу в режиме «без исключения», возвращается `null` либо формула `"#000000"`. В закомментированном коде того же класса видна проверка цвета по шаблону `#RRGGBB` / `#AARRGGBB`: цвета в параметрах блоков, судя по этому, записываются строками в таком формате.
- Метод `updateUserDataReference` переименовывает переменные и списки внутри формул: ссылки на `USER_VARIABLE` и `USER_LIST` хранятся именами (см. 6.13).
- Аннотации `@XStreamFieldKeyOrder` в `FormulaBrick` нет, есть только `@XStreamAlias`. Порядок полей, если он где-то задан, определяется другими классами.

### 6.20. Таблица «блок → поля формул» (`addAllowedBrickField`)

Таблица собрана из выгрузки вызовов `addAllowedBrickField` по каталогу `content/bricks` (команда `grep -rn "addAllowedBrickField\|^public class"`, 1892 строки). Для каждого блока поле формул это значение `BrickField`, то есть допустимая `category` в `<formula category="…">` (см. 6.1 и 6.19).

**Как читать**
- Порядок полей такой же, как порядок вызовов в конструкторе; обычно он совпадает с порядком параметров в блоке на экране.
- Если класс вызывает одно и то же поле несколько раз (так в `TurnLeftBrick`, `TurnRightBrick`, `SetGravityBrick`), поле считается одним: карта формул `ConcurrentFormulaHashMap` хранит каждый ключ один раз.
- Поля унаследованных блоков учтены: `SayForBubbleBrick` получает поля `ThinkForBubbleBrick`, `SayBubbleBrick` поля `ThinkBubbleBrick`, `RaspiIfLogicBeginBrick` поле `IF_CONDITION` от `IfLogicBeginBrick`.
- Список показывает **только формульные параметры**. Выбор из выпадающего списка, образ, звук, сообщение, переменная, список и подобные поля к `formulaList` не относятся и здесь не перечислены (см. «Блоки без формул-параметров» ниже). Они описаны в 6.21.

**Покрытие**

| Показатель | Значение |
|---|---|
| Классов с суффиксом `Brick` в каталоге | 646 |
| Из них есть в выгрузке | 618 |
| Из них с хотя бы одним формульным полем | 489 |
| Без формульных полей | 129 |
| Нет в выгрузке | 28 |
| Вызов разбит на строки, поле не видно | 4: `SavePlotBrick`, `SetBackgroundByIndexAndWaitBrick`, `SetCameraFocusPointBrick`, `WriteEmbroideryToFileBrick` |

Не вошли в выгрузку 28 классов: `Brick`, `BroadcastMessageBrick`, `CameraBrick`, `ChooseCameraBrick`, `ChooseFileBrick`, `CompositeBrick`, `DeleteLookBrick`, `EditLookBrick`, `EndBrick`, `FadeParticleEffectBrick`, `ListSelectorBrick`, `NativeLayerBrick`, `NextLookBrick`, `NoneBrick`, `ParameterizedBrick`, `ParticleEffectAdditivityBrick`, `PreviousLookBrick`, `ScriptBrick`, `SetListeningLanguageBrick`, `StartListeningBrick`, `StartPlotBrick`, `StopPlotBrick`, `StopSoundBrick`, `SubCategoryHeaderBrick`, `UserDataBrick`, `UserListBrick`, `UserVariableBrick`, `VisualPlacementBrick`. Среди них служебные (`Brick`, `CompositeBrick`, `ScriptBrick`, `EndBrick`, `NoneBrick` и т. п.) и 20 классов на Kotlin: поиск `addAllowedBrickField` шёл и по `.kt`-файлам, поэтому у таких классов собственных формульных полей нет (унаследованные от базового класса в выгрузке не видны). Остальные 8 не имеют ни вызовов `addAllowedBrickField`, ни объявления `public class` в начале строки: `Brick`, `BroadcastMessageBrick`, `CompositeBrick`, `ScriptBrick`, `UserDataBrick`, `UserListBrick`, `UserVariableBrick`, `VisualPlacementBrick`; их формульные поля неизвестны.

**Базовые классы и что они означают**

| Базовый класс | Блоков | Смысл |
|---|---|---|
| `FormulaBrick` | 449 | блок с формульными параметрами (в том числе 19 без параметров вообще) |
| `BrickBaseType` | 66 | блок без формульных параметров |
| `UserVariableBrickWithFormula` | 27 | блок работы с переменной и формулой (например, `SetVariableBrick`) |
| `ScriptBrickBaseType` | 22 | блок-шапка скрипта (список ниже) |
| `UserListBrick` | 10 | блок работы со списком |
| `UserVariableBrickWithVisualPlacement` | 6 | блок переменной с позицией на экране |
| `VisualPlacementBrick` | 4 | блок с позицией на экране (`PlaceAtBrick`, `SquareBrick` и др.) |
| `UserVariableBrick`, `UserDataBrick`, `BroadcastMessageBrick` | 3, 2, 2 | базовые типы переменных, пользовательских данных и сообщений |

**Блоки-шапки скриптов** (наследуют `ScriptBrickBaseType`, 22): `EmptyEventBrick`, `UserDefinedReceiverBrick`, `WhenAfterUpdateBrick`, `WhenAppMinimizedBrick`, `WhenAppRestoredBrick`, `WhenBackPressedBrick`, `WhenBeforeUpdateBrick`, `WhenBounceOffBrick`, `WhenBrick`, `WhenClonedBrick`, `WhenFingerMovedOnScreenBrick`, `WhenFingerMovedOverSpriteBrick`, `WhenGamepadButtonBrick`, `WhenMouseButtonClickedBrick`, `WhenMouseWheelScrolledBrick`, `WhenNfcBrick`, `WhenProjectExitsBrick`, `WhenRaspiPinChangedBrick`, `WhenSpriteReleasedBrick`, `WhenStartedBrick`, `WhenTouchDownBrick`, `WhenWindowResizedBrick`.

**Динамические и пользовательские блоки.** В `CustomBrick`, `UserDefinedBrick` и `FormulaBrick` вызов `addAllowedBrickField` принимает поле как переменную (`formulaField`, `brickField`), а не константу. Значит, у пользовательских блоков ключи формул могут быть не из `BrickField`; это согласуется с выводом из 6.19: помимо `BrickField` интерфейс `FormulaField` реализует `InputFormulaField` (пользовательские блоки, 6.26).

**Блоки без формул-параметров** (по базовому классу):
- `BrickBaseType` (66): `ClearBackgroundBrick`, `ClearGraphicEffectBrick`, `ClearSceneBrick`, `CloneBrick`, `ComeToFrontBrick`, `DeleteThisCloneBrick`, `DeleteVarsBrick`, `DroneEmergencyBrick`, `DroneFlipBrick`, `DronePlayLedAnimationBrick`, `DroneSwitchCameraBrick`, `DroneTakeOffLandBrick`, `ExitStageBrick`, `FinishStageBrick`, `FlashBrick`, `ForeverBrick`, `GoToBrick`, `HideBrick`, `IfLogicElseBrick`, `IfLogicEndBrick`, `IfOnEdgeBounceBrick`, `IfThenLogicEndBrick`, `InstantBrick`, `JumpingSumoAnimationsBrick`, `JumpingSumoJumpHighBrick`, `JumpingSumoJumpLongBrick`, `JumpingSumoNoSoundBrick`, `JumpingSumoTakingPictureBrick`, `JumpingSumoTurnBrick`, `LegoEv3MotorStopBrick`, `LegoEv3SetLedBrick`, `LegoNxtMotorStopBrick`, `LockMouseBrick`, `LoopEndBrick`, `PenDownBrick`, `PenUpBrick`, `PhiroIfLogicBeginBrick`, `PhiroMotorStopBrick`, `PinToCameraBrick`, `PlaySoundBrick`, `PointToBrick`, `ResetTimerBrick`, `ReturnToPreviousProjectBrick`, `SceneStartBrick`, `SceneTransitionBrick`, `SetBackgroundBrick`, `SetHitboxBrick`, `SetInstrumentBrick`, `SetLookBrick`, `SetPhysicsObjectTypeBrick`, `SetRotationStyleBrick`, `ShowBrick`, `StampBrick`, `StartRecordingBrick`, `StitchBrick`, `StopAllSoundsBrick`, `StopRunningStitchBrick`, `StopScriptBrick`, `TestBrick`, `TryCatchFinallyBrick`, `UnknownBrick`, `UnlockMouseBrick`, `UnpinFromCameraBrick`, `UpdateScreenBrick`, `WaitTillIdleBrick`, `WhenBackgroundChangesBrick`.
- `FormulaBrick`, но без параметров (19): `ClearPythonEnvironmentBrick`, `DeleteAllTablesBrick`, `DisableBackgroundModeBrick`, `EnablePbrRenderBrick`, `HideStatusBarBrick`, `OrientationBrick`, `PenFlushBrick`, `PhotoBrick`, `PtZeroGradBrick`, `ScreenShotBrick`, `SetFreeCameraBrick`, `SewUpBrick`, `StopBufferRecordingBrick`, `StopGifBrick`, `StopServerBrick`, `StopSpritesheetBrick`, `StopVMBrick`, `UnloadNNBrick`, `UserDefinedBrick`.
- Прочие: `UserListBrick` `ClearUserListBrick`, `ReadListFromDeviceBrick`, `WriteListOnDeviceBrick`; `UserVariableBrick` `HideTextBrick`, `ReadVariableFromDeviceBrick`, `WriteVariableOnDeviceBrick`; `UserDataBrick` `AssertUserListsBrick`, `ForItemInUserListBrick`; `UserVariableBrickWithFormula` `BindVmOutputBrick`, `ListenServerBrick`; `BroadcastMessageBrick` `BroadcastBrick`, `BroadcastReceiverBrick`; `BroadcastBrick` `BroadcastWaitBrick`; `LoopEndBrick` `LoopEndlessBrick`; `PlaySoundBrick` `PlaySoundAndWaitBrick`; `SetBackgroundBrick` `SetBackgroundAndWaitBrick`; базовый класс не определён `CustomBrick`, `FormulaBrick`, `SavePlotBrick`, `SetBackgroundByIndexAndWaitBrick`, `SetCameraFocusPointBrick`, `WriteEmbroideryToFileBrick`.

У блоков с базой `UserVariableBrickWithFormula` без собственных вызовов (и у подобных) поля могут задаваться базовым классом, которого в выгрузке нет.

**Чаще всего используемые поля:** `VALUE_1` (119), `VALUE_2` (96), `NAME` (93), `VALUE_3` (65), `VALUE_4` (44), `X_POSITION` (43), `Y_POSITION` (42), `VALUE` (36), `TEXT` (28), `FILE` (27), `VALUE_5` (22), `HEIGHT` (17). Универсальные `VALUE_1`…`VALUE_N` и `NAME` встречаются в новых блоках NewCatroid, где нет отдельного названного поля.

**Значения `BrickField`, которые ни один блок из каталога не регистрирует** (31): `BACKGROUND_WAIT_INDEX`, `CUSTOM_PARAM_1`, `CUSTOM_PARAM_10`, `CUSTOM_PARAM_2`, `CUSTOM_PARAM_3`, `CUSTOM_PARAM_4`, `CUSTOM_PARAM_5`, `CUSTOM_PARAM_6`, `CUSTOM_PARAM_7`, `CUSTOM_PARAM_8`, `CUSTOM_PARAM_9`, `DRONE_ALTITUDE_LIMIT`, `DRONE_ROTATION_MAX`, `DRONE_TILT_ANGLE`, `DRONE_VERTICAL_SPEED_MAX`, `FORMULA_5`, `FORMULA_6`, `FORMULA_7`, `HIDE_STATUS_BAR`, `HORIZONTAL_FLEXIBILITY`, `LEGO_EV3_PERIOD_IN_SECONDS`, `LEGO_EV3_POWER`, `ROTATION_STYLE`, `SHOWTEXT`, `STRING_VALUE`, `TEST_FORMULA`, `THREED_ENABLED`, `USER_BRICK`, `USER_DEFINED`, `VERTICAL_FLEXIBILITY`, `VM_NAME`. Это либо устаревшие и зарезервированные поля, либо поля, используемые вне каталога `content/bricks` (например, в пользовательских блоках); по выгрузке различить нельзя.

**Сверка с wiki.** Для 591 блока, у которого есть страница wiki и запись в выгрузке, число строк в таблице «Параметры» совпадает с числом формульных полей класса у 326, у 133 в wiki параметров меньше, у 132 больше. Судя по примерам (`broadcast`, `clone`: в wiki один параметр, формульных полей нет), «больше» бывает там, где wiki перечисляет неформульные параметры (сообщение, выбор из списка); «меньше» там, где wiki пропускает часть формул. Это вывод по выборочным примерам, а не проверка всех 265 расхождений. Часть расхождений может объясняться тем, что wiki местами описывает версию 2.3.0, а код относится к 2.2.0. Поэтому для списка допустимых `category` источником считать нужно эту таблицу, а не страницу wiki.

**Таблица по блокам** (`ИмяКласса: поле1, поле2, …`, 489 блоков):

```
AddEditBrick: NAME, TEXT
AddFileToApkBrick: TEXT_1, TEXT_2, TEXT_3
AddHingeBrick: CONSTRAINT_ID, OBJECT_A, OBJECT_B, PIVOT_A_X, PIVOT_A_Y, PIVOT_A_Z, AXIS_A_X, AXIS_A_Y, AXIS_A_Z, PIVOT_B_X, PIVOT_B_Y, PIVOT_B_Z, AXIS_B_X, AXIS_B_Y, AXIS_B_Z
AddItemToUserListBrick: LIST_ADD_ITEM
AddRadioBrick: NAME, TEXT
AddTextToBufferBrick: IF_CONDITION, INSERT_ITEM_INTO_USERLIST_VALUE
AddToBufferBrick: NAME
Apply3dForceBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
Apply3dTorqueBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
ApplyAngularImpulseBrick: ANGULAR_IMPULSE
ApplyBufferLookBrick: NAME
ApplyForceBrick: FORCE_X, FORCE_Y
ApplyImpulseBrick: IMPULSE_X, IMPULSE_Y
ApplyShaderBrick: NAME, TEXT, VALUE_1
ApplyShaderToImageBrick: NAME, TEXT, X_POSITION
ApplyTorqueBrick: TORQUE
ArduinoSendDigitalValueBrick: ARDUINO_DIGITAL_PIN_NUMBER, ARDUINO_DIGITAL_PIN_VALUE
ArduinoSendPWMValueBrick: ARDUINO_ANALOG_PIN_NUMBER, ARDUINO_ANALOG_PIN_VALUE
AskBrick: ASK_QUESTION
AskGPTBrick: TEXT, BODY
AskGemini2Brick: QUESTION, MODEL
AskGeminiBrick: QUESTION
AskSpeechBrick: ASK_SPEECH_QUESTION
AssertEqualsBrick: ASSERT_EQUALS_ACTUAL, ASSERT_EQUALS_EXPECTED
AsyncRepeatBrick: TIMES_TO_REPEAT
AttachRaySensorBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7, VALUE_8, VALUE_9
AttachSOBrick: GL_VIEW_NAME, FILE
AttachToCameraBrick: NAME
BackgroundRequestBrick: BACKGROUND_REQUEST
BakeByPrefixBrick: VALUE_1, VALUE_2
Base64ToFileBrick: VALUE_1, VALUE_2
BigAskBrick: ASK_QUESTION, TEXT, OK, CANEL, DEFAULT
BroadcastWithParamsBrick: VALUE_1, VALUE_2
BroadcastWithParamsReceiverBrick: VALUE_1
BufferMaskBrick: VALUE_1
CameraLookAtBrick: VALUE, VALUE_2, VALUE_3
CameraSettingsBrick: FOV, INTENSITY, DURATION
CameraTouchControlBrick: ENABLED, SENSITIVITY, X, Y, WIDTH, HEIGHT
CameraTrackingBrick: NAME, X_POSITION, Y_POSITION, Z_POSITION, YAW, PITCH, ROLL
CastRayBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7
ChangeBrightnessByNBrick: BRIGHTNESS_CHANGE
ChangeColorByNBrick: COLOR_CHANGE
ChangeHeightBrick: SIZE
ChangeSizeByNBrick: SIZE_CHANGE
ChangeTempoByNBrick: TEMPO_CHANGE
ChangeTransparencyByNBrick: TRANSPARENCY_CHANGE
ChangeVariableBrick: VARIABLE_CHANGE
ChangeVolumeByNBrick: VOLUME_CHANGE
ChangeWidthBrick: SIZE
ChangeXByNBrick: X_POSITION_CHANGE
ChangeYByNBrick: Y_POSITION_CHANGE
CloneAndNameBrick: CLONE_NAME
CloneObjectBrick: VALUE_1, VALUE_2
ConfigureLightBrick: VALUE_1, VALUE_2
ConfigureMaterialBrick: VALUE_1, VALUE_2
ConfigureParticlesBrick: VALUE_1, VALUE_2
ConnectServerBrick: IP, PORT
CopyLookBrick: LOOK_COPY
CopyProjectFileBrick: NAME, TEXT
CopyTextBrick: TEXT
Create3dObjectBrick: VALUE, VALUE_2
CreateBufferBrick: NAME, WIDTH, HEIGHT
CreateButtonBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, X_POSITION, Y_POSITION, WIDTH, HEIGHT
CreateCubeBrick: VALUE
CreateDialogBrick: NAME, TITLE, MESSAGE
CreateDiskBrick: VM_DISK_NAME, VM_DISK_SIZE
CreateDistanceJointBrick: JOINT_ID, SPRITE, JOINT_LENGTH, JOINT_FREQUENCY, JOINT_DAMPING
CreateFloatBrick: FLOAT_ARRAY
CreateGLViewBrick: GL_VIEW_NAME, X_POSITION, Y_POSITION, WIDTH, HEIGHT
CreateGearJointBrick: JOINT_ID, JOINT_A_ID, JOINT_B_ID, RATIO
CreateImageViewBrick: VALUE_1, VALUE_2, VALUE_3, X_POSITION, Y_POSITION, WIDTH, HEIGHT
CreateParticleEffectBrick: FILE
CreateParticlesBrick: PARTICLE_ID, PARTICLE_LOOPING, PARTICLE_DURATION, PARTICLE_LIFETIME, PARTICLE_SPEED, PARTICLE_SIZE, PARTICLE_END_SIZE, PARTICLE_GRAVITY, PARTICLE_MAX_COUNT, PARTICLE_RATE, PARTICLE_ANGLE, PARTICLE_RADIUS, PARTICLE_START_COLOR, PARTICLE_END_COLOR, PARTICLE_TEXTURE, PARTICLE_ADDITIVE, PARTICLE_ROTATION, PARTICLE_ROTATION_SPEED, PARTICLE_POS_X, PARTICLE_POS_Y, PARTICLE_POS_Z, PARTICLE_ROT_PITCH, PARTICLE_ROT_YAW, PARTICLE_ROT_ROLL
CreatePointJointBrick: JOINT_NAME, OBJECT_A, OBJECT_B, PIVOT_A_X, PIVOT_A_Y, PIVOT_A_Z, PIVOT_B_X, PIVOT_B_Y, PIVOT_B_Z
CreatePrismaticJointBrick: JOINT_ID, SPRITE, X_POSITION, Y_POSITION, AXIS_X, AXIS_Y
CreatePulleyJointBrick: JOINT_ID, SPRITE_A, SPRITE_B, GROUND_ANCHOR_A_X, GROUND_ANCHOR_A_Y, GROUND_ANCHOR_B_X, GROUND_ANCHOR_B_Y, RATIO
CreateRevoluteJointBrick: JOINT_ID, SPRITE, X_POSITION, Y_POSITION
CreateScrollViewBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, X_POSITION, Y_POSITION, WIDTH, HEIGHT
CreateSliderBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, X_POSITION, Y_POSITION, WIDTH, HEIGHT
CreateSphereBrick: VALUE_1
CreateSpringConstraintBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7, VALUE_8, VALUE_9, VALUE_10, VALUE_11, VALUE_12, VALUE_13, VALUE_14, VALUE_15, VALUE_16, VALUE_17
CreateSwitchBrick: VALUE_1, VALUE_2, VALUE_3, X_POSITION, Y_POSITION, WIDTH, HEIGHT
CreateTableBrick: TABLE_NAME, SIZE_X, SIZE_Y
CreateTextFieldBrick: NAME, TEXT, X_POSITION, Y_POSITION, WIDTH, HEIGHT, TEXTSIZE, TEXTCOLOR, BGCOLOR, HINT_TEXT, HINT_COLOR, ALIGNMENT, PASSWORD, FILE, CORNER, MAX_LEN, TYPE
CreateTextLabelBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7, VALUE_8, X_POSITION, Y_POSITION, WIDTH, HEIGHT
CreateVarBrick: VARNAME, VALUE
CreateVideoBrick: NAME, FILE, POSX, POSY, WIDTH, HEIGHT, LOOPED, CONTROLS
CreateWebFileBrick: NAME, HTML, POSX, POSY, WIDTH, HEIGHT
CreateWebUrlBrick: NAME, URL, POSX, POSY, WIDTH, HEIGHT
CreateWeldJointBrick: JOINT_ID, SPRITE, X_POSITION, Y_POSITION
CutLookBrick: X1, Y1, X2, Y2
DelSquareBrick: NAME
DeleteBaseBrick: FIREBASE_ID, FIREBASE_KEY
DeleteFilesBrick: VALUE
DeleteFloatBrick: LOOK_INDEX, FLOAT_ARRAY
DeleteFromApkBrick: TEXT_1, TEXT_2
DeleteItemOfUserListBrick: LIST_DELETE_ITEM
DeleteParticlesBrick: PARTICLE_ID
DeleteTableBrick: TABLE_NAME
DeleteVarBrick: VARNAME
DeleteWebBrick: NAME
DestroyJointBrick: JOINT_ID
DetachFromCameraBrick: NAME
DroneMoveBackwardBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
DroneMoveDownBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
DroneMoveForwardBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
DroneMoveLeftBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
DroneMoveRightBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
DroneMoveUpBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
DroneTurnLeftBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
DroneTurnRightBrick: DRONE_TIME_TO_FLY_IN_SECONDS, DRONE_POWER_IN_PERCENT
Ease3DPropertyBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
EasePropertyBrick: IF_CONDITION, INSERT_ITEM_INTO_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_VALUE
ElseIfSeparatorBrick: IF_CONDITION
EmitParticleBurstBrick: NAME, VALUE_1
EnableBackgroundModeBrick: VALUE_1, VALUE_2
EvalWebBrick: CODE, NAME
Export3dObjectToGlbBrick: VALUE_1, VALUE_2
ExportProjectFileBrick: NAME
ExtractFileBrick: TEXT_1, TEXT_2, TEXT_3
Fast2DApplyForceBrick: NAME, X_POSITION, Y_POSITION
Fast2DApplyImpulseBrick: NAME, X_POSITION, Y_POSITION
Fast2DCreateBrick: NAME
Fast2DDeleteBrick: NAME
Fast2DMakePhysicsBrick: NAME, X_POSITION, STRING, Y_POSITION, ROTATION, SIZE
Fast2DSetAngularVelocityBrick: NAME, ROTATION
Fast2DSetCameraBrick: X_POSITION, Y_POSITION, SIZE
Fast2DSetCollisionFilterBrick: NAME, X_POSITION, Y_POSITION
Fast2DSetColorBrick: NAME, X_POSITION, Y_POSITION, ROTATION, SIZE
Fast2DSetGravityBrick: VALUE_1, VALUE_2
Fast2DSetPhysicsVelocityBrick: NAME, X_POSITION, Y_POSITION
Fast2DSetPositionBrick: NAME, X_POSITION, Y_POSITION
Fast2DSetRotationBrick: NAME, ROTATION
Fast2DSetScaleBrick: NAME, X_SCALE, Y_SCALE
Fast2DSetTextureBrick: NAME, STRING
Fast2DSetVelocityBrick: NAME, X_POSITION, Y_POSITION
Fast2DSetZIndexBrick: NAME, VIBRATE_DURATION
FileUrlBrick: FILE_URL, FILE
FilesUrlBrick: FILE_URL, FILE
ForVariableFromToBrick: FOR_LOOP_FROM, FOR_LOOP_TO
GenerateKeyBrick: TEXT_1, TEXT_2, TEXT_3, TEXT_4
GetZipFileNamesBrick: NAME
GlideToBrick: X_DESTINATION, Y_DESTINATION, DURATION_IN_SECONDS
GoNStepsBackBrick: STEPS
GrayscaleImgBrick: FILE
HideText3Brick: NAME
HttpAttachFileBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
HttpBodyBrick: VALUE_1, VALUE_2, VALUE_3
HttpConfigBrick: VALUE_1, VALUE_2, VALUE_3
HttpCreateBrick: VALUE_1, VALUE_2, VALUE_3
HttpSaveFileBrick: VALUE_1, VALUE_2
HttpSendBrick: VALUE_1
IfLogicBeginBrick: IF_CONDITION
IfThenLogicBeginBrick: IF_CONDITION
InsertItemIntoUserListBrick: INSERT_ITEM_INTO_USERLIST_VALUE, INSERT_ITEM_INTO_USERLIST_INDEX
InsertTableBrick: TABLE_NAME, VALUE, SIZE_X, SIZE_Y
IntervalRepeatBrick: TIMES_TO_REPEAT, INTERVAL
JavaCompileBrick: VALUE_1, VALUE_2
JavaDownloadDepBrick: VALUE_1, VALUE_2
JavaLoadAndRunBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
JumpingSumoMoveBackwardBrick: JUMPING_SUMO_TIME_TO_DRIVE_IN_SECONDS, JUMPING_SUMO_SPEED
JumpingSumoMoveForwardBrick: JUMPING_SUMO_TIME_TO_DRIVE_IN_SECONDS, JUMPING_SUMO_SPEED
JumpingSumoRotateLeftBrick: JUMPING_SUMO_ROTATE
JumpingSumoRotateRightBrick: JUMPING_SUMO_ROTATE
JumpingSumoSoundBrick: JUMPING_SUMO_VOLUME
KeyEventBrick: VALUE, VM_KEY_DOWN
KeyframeAnimationBrick: VALUE_1, VALUE_2
LaunchProjectBrick: PROJECT_NAME
LegoEv3MotorMoveBrick: LEGO_EV3_SPEED
LegoEv3MotorTurnAngleBrick: LEGO_EV3_DEGREES
LegoEv3PlayToneBrick: LEGO_EV3_FREQUENCY, LEGO_EV3_DURATION_IN_SECONDS, LEGO_EV3_VOLUME
LegoNxtMotorMoveBrick: LEGO_NXT_SPEED
LegoNxtMotorTurnAngleBrick: LEGO_NXT_DEGREES
LegoNxtPlayToneBrick: LEGO_NXT_FREQUENCY, LEGO_NXT_DURATION_IN_SECONDS
ListenMicroBrick: TIME
LoadFromInternalStorageBrick: FILE_NAME
LoadNNBrick: FILE
LoadNativeModuleBrick: FILE_NAME
LoadPythonLibraryBrick: FILE_NAME
LoadSceneAdditiveBrick: TEXT
LoadSceneBrick: VALUE
LookFileBrick: FILE
LookFromTableBrick: RED, GREEN, BLUE, ALPHA
LookRequestBrick: LOOK_REQUEST
LookToTableBrick: RED, GREEN, BLUE, ALPHA
LunoScriptBrick: CODE
MLLoadBrick: STRING
MLSaveBrick: STRING
MLStepAdamBrick: VALUE
MLStepAdamWBrick: VALUE_1, VALUE_2
MouseEventBrick: X_POSITION, Y_POSITION, VALUE
MoveDownloadsBrick: FILE
MoveFilesBrick: FILE
MoveNStepsBrick: STEPS
MqttConnectBrick: VALUE_1, VALUE_2, VALUE_3
MqttDisconnectBrick: VALUE_1
MqttJoinRoomBrick: VALUE_1, VALUE_2, VALUE_3
MqttPublishBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
NativeViewAnimateBrick: VALUE_1, VALUE_2, VALUE_3
NativeViewBindSpriteBrick: VALUE_1, VALUE_2, X_POSITION, Y_POSITION
NativeViewConfigBrick: VALUE_1, VALUE_2
NativeViewControlBrick: VALUE_1, VALUE_2
NativeViewListenerBrick: VALUE_1
NormalizeImgBrick: FILE, RED, GREEN, BLUE
NoteBrick: NOTE
NotificationAddButtonBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
NotificationCancelBrick: VALUE_1
NotificationCreateBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
NotificationShowBrick: VALUE_1, VALUE_2
ObjectLookAtBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
ObjectLookAtCorrectBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
OpenAppBrick: VALUE_1
OpenFileBrick: FILE
OpenFilesBrick: FILE
OpenUrlBrick: OPEN_URL
PaintNewLookBrick: LOOK_NEW
ParameterizedEndBrick: ASSERT_LOOP_ACTUAL
PauseForBeatsBrick: BEATS_TO_PAUSE
PauseVideoBrick: NAME
PenClearColorBrick: COLOR, VALUE
PenDrawCircleBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6
PenDrawLineBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
PenDrawRectBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
PenDrawTriangleBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7
PerformRayCastBrick: RAY_ID, X_START, Y_START, X_END, Y_END
PhiroMotorMoveBackwardBrick: PHIRO_SPEED
PhiroMotorMoveForwardBrick: PHIRO_SPEED
PhiroPlayToneBrick: PHIRO_DURATION_IN_SECONDS
PhiroRGBLightBrick: PHIRO_LIGHT_RED, PHIRO_LIGHT_GREEN, PHIRO_LIGHT_BLUE
PlaceAtBrick: X_POSITION, Y_POSITION
PlayAnimationBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
PlayDrumForBeatsBrick: PLAY_DRUM
PlayGifBrick: VALUE_1
PlayNoteForBeatsBrick: NOTE_TO_PLAY, BEATS_TO_PLAY_NOTE
PlayPreparedSoundBrick: CACHE_NAME
PlaySoundAtBrick: PLAY_SOUND_AT
PlaySoundAtPositionBrick: SOUND_NAME, INSTANCE_NAME, POS_X, POS_Y, POS_Z, VOLUME, PITCH
PlaySpritesheetBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
PlayVideoBrick: NAME
PointInDirectionBrick: DEGREES
PostWebRequestBrick: URL, HEADER, BODY
PredictNNBrick: VALUE
PrepareMusicAs3DSoundBrick: FILE_NAME, SOUND_NAME
PrepareSoundBrick: FILE_NAME, CACHE_NAME
PromoteLightBrick: NAME
PtAttentionBrick: NAME, VALUE_1, VALUE_2, VALUE_3
PtBackwardBrick: NAME
PtClipGradBrick: VALUE_1
PtConv2DBrick: NAME, VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6
PtCreateNormalTensorBrick: NAME, VALUE_1, VALUE_2, VALUE_3, VALUE_4
PtCreateTensorBrick: NAME, VALUE_1, VALUE_2, VALUE_3
PtDropoutBrick: NAME, VALUE_1, VALUE_2
PtEmbeddingBrick: NAME, VALUE_1, VALUE_2, VALUE_3, VALUE_4
PtGruCellBrick: NAME, VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
PtLayerLinearBrick: NAME, VALUE_1, VALUE_2, VALUE_3, VALUE_4
PtLstmCellBrick: NAME, VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7
PtMaxPool2DBrick: NAME, VALUE_1, VALUE_2, VALUE_3
PtOpBrick: VALUE_1, VALUE_2, VALUE_3
PtReshapeBrick: NAME, VALUE_1
PtSetByIndexBrick: NAME, VALUE_1, VALUE_2
PtSetTensorBrick: NAME, VALUE_1
PtSetTrainingBrick: VALUE_1
PtSliceBrick: NAME, VALUE_1, VALUE_2, VALUE_3
PtStepBrick: VALUE_1
PutFloatBrick: FLOAT_ARRAY, VALUE, LOOK_INDEX
RaspiIfLogicBeginBrick: IF_CONDITION
RaspiPwmBrick: RASPI_DIGITAL_PIN_NUMBER, RASPI_PWM_FREQUENCY, RASPI_PWM_PERCENTAGE
RaspiSendDigitalValueBrick: RASPI_DIGITAL_PIN_NUMBER, RASPI_DIGITAL_PIN_VALUE
ReadBaseBrick: FIREBASE_ID, FIREBASE_KEY
ReadFromFilesBrick: VALUE
ReadVariableFromFileBrick: READ_FILENAME
RegexBrick: TEXT, REGEX
Remove3dObjectBrick: VALUE
RemoveFromBufferBrick: NAME
RemoveJointBrick: JOINT_NAME
RemoveObjectsByPrefixBrick: VALUE
RemoveParentBrick: CHILD_OBJECT
RemovePbrLightBrick: VALUE_1
RepeatBrick: TIMES_TO_REPEAT
RepeatUntilBrick: REPEAT_UNTIL_CONDITION
Replace3DModelBrick: NAME, TEXT
ReplaceItemInUserListBrick: REPLACE_ITEM_IN_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_INDEX
ReportBrick: REPORT_BRICK
ResizeImgBrick: FILE, WIDTH, HEIGHT
RotateCameraByBrick: PITCH, YAW, ROLL
RunAsSpriteBrick: NAME
RunChip8Brick: TEXT
RunJSBrick: CODE
RunLuaBrick: CODE
RunPythonScriptBrick: SCRIPT, VARIABLE_NAME
RunShellBrick: CODE
RunVMBrick: VM_MEMORY, VM_CPU, VM_HDA, VM_CDROM
RunVm2Brick: VM_ARGUMENTS
RunningStitchBrick: EMBROIDERY_LENGTH
SaveBufferBrick: NAME
SaveLookBrick: FILE
SaveLookFilesBrick: FILE
SaveToInternalStorageBrick: PROJECT_FILE_NAME, FILE_NAME
SayBubbleBrick: STRING
SayForBubbleBrick: STRING, DURATION_IN_SECONDS
SceneIdBrick: SCENE_ID
SeekVideoBrick: NAME, TIME
SendServerBrick: VALUE
SendVmInputBrick: INPUT_TEXT
Set3DSoundMaxDistanceBrick: INSTANCE_NAME, DISTANCE
Set3DSoundPositionBrick: NAME, VALUE_X, VALUE_Y, VALUE_Z
Set3dFrictionBrick: VALUE_1, VALUE_2
Set3dGravityBrick: VALUE_2, VALUE_3, VALUE_4
Set3dPositionBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
Set3dRotationBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
Set3dScaleBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
Set3dVelocityBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
SetAIBrick: OBJECT_ID, MODE, TARGET, SPEED, DISTANCE, RANGE, STEP_HEIGHT, AVOID_OBSTACLES
SetActiveBrick: OBJECT_NAME
SetAmbientLightBrick: VALUE_1, VALUE_2, VALUE_3
SetAnimationSpeedBrick: OBJECT_ID, SPEED
SetAnisotropicFilterBrick: VALUE_1, VALUE_2
SetBackgroundByIndexBrick: BACKGROUND_INDEX
SetBackgroundLightBrick: VALUE_1
SetBounceBrick: PHYSICS_BOUNCE_FACTOR
SetBrightnessBrick: BRIGHTNESS
SetBufferAutoUpdateBrick: NAME
SetBufferCamera3DBrick: NAME, X_POSITION, Y_POSITION, Z_POSITION, DEGREES, DEGREES_BY, ROTATION, SIZE
SetBufferCameraBrick: NAME, X_POSITION, Y_POSITION, ZOOM, DEGREES
SetBufferEffectsBrick: IF_CONDITION, INSERT_ITEM_INTO_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_VALUE
SetBufferModeBrick: NAME, X_POSITION, Y_POSITION
SetBufferOnlyBrick: TIME
SetBufferShaderBrick: IF_CONDITION, INSERT_ITEM_INTO_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_VALUE
SetBufferShaderUniformBrick: IF_CONDITION, INSERT_ITEM_INTO_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_VALUE, INSERT_ITEM_INTO_USERLIST_INDEX, TIMES_TO_REPEAT
SetCCDBrick: THREED_OBJECT_ID
SetCallbackBrick: NAME
SetCameraPosition2Brick: X_POSITION, Y_POSITION
SetCameraPositionBrick: VALUE, VALUE_2, VALUE_3
SetCameraRangeBrick: VALUE_1, VALUE_2
SetCameraRotation2Brick: DEGREES
SetCameraRotationBrick: VALUE_1, VALUE_2, VALUE_3
SetCameraZoomBrick: VALUE
SetColorBrick: COLOR
SetCornerOffsetsBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7, VALUE_8
SetDampingBrick: LINEAR_DAMPING, ANGULAR_DAMPING
SetDirectionalLight2Brick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
SetDirectionalLightBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7
SetDnsBrick: VALUE
SetEmissiveBrick: OBJECT_NAME, RED, GREEN, BLUE, ALPHA, INTENSITY, MATERIAL_TEXTURE_COLOR
SetFogBrick: FORMULA_1, FORMULA_2, FORMULA_3, FORMULA_4
SetFpsBrick: VALUE
SetFrictionBrick: PHYSICS_FRICTION
SetGeminiKeyBrick: KEY
SetGlobalSoundVolumeBrick: VOLUME
SetGravityBrick: PHYSICS_GRAVITY_X, PHYSICS_GRAVITY_Y
SetHeightBrick: SIZE
SetHingeMotorBrick: CONSTRAINT_ID, MOTOR_TARGET, MOTOR_MAX_FORCE
SetLookByIndexBrick: LOOK_INDEX
SetLookFilesBrick: FILE
SetMainRenderLoopsBrick: IF_CONDITION, INSERT_ITEM_INTO_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_VALUE
SetMassBrick: PHYSICS_MASS
SetMaterialBrick: OBJECT_NAME, MATERIAL_R, MATERIAL_G, MATERIAL_B, MATERIAL_A, MATERIAL_METALLIC, MATERIAL_ROUGHNESS, MATERIAL_TEXTURE_COLOR, MATERIAL_TEXTURE_NORMAL, MATERIAL_TEXTURE_MR
SetMaxPointLightsBrick: MAX_LIGHTS
SetNativeParentBrick: VALUE_1, VALUE_2
SetNegativeBrick: NAME, TEXT
SetNeutralBrick: NAME, TEXT
SetNfcTagBrick: NFC_NDEF_MESSAGE
SetObjectColorBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
SetObjectShaderBrick: NAME, TEXT, VALUE
SetObjectShaderUniformBrick: NAME, TEXT, X, Y, Z
SetObjectTextureBrick: VALUE, VALUE_2
SetParentBrick: CHILD_OBJECT, PARENT_OBJECT
SetParticleBufferRenderBrick: NAME, TEXT
SetParticleColorBrick: COLOR
SetParticleEmissionBrick: OBJECT_ID, EMISSION_RATE
SetParticlePropertyBrick: NAME, VALUE_1
SetParticleTransformBrick: NAME, X, Y, VALUE_1, VALUE_2, VALUE_3
SetPenColorBrick: PEN_COLOR_RED, PEN_COLOR_GREEN, PEN_COLOR_BLUE
SetPenPropertyBrick: VALUE
SetPenSizeBrick: PEN_SIZE
SetPhysicsStateBrick: VALUE_1, VALUE_2
SetPointLightBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7, VALUE_8, VALUE_9
SetPositiveBrick: NAME, TEXT
SetPostProcessingBrick: VALUE
SetPostProcessingNewBrick: VALUE
SetRenderResolutionBrick: NAME, VALUE
SetRestitutionBrick: VALUE_1, VALUE_2
SetRotationLockBrick: STRING
SetSaveScenesBrick: VALUE
SetScreenShaderBrick: VERTEX, FRAGMENT
SetShaderCodeBrick: THREED_VERTEX_SHADER_CODE, THREED_FRAGMENT_SHADER_CODE
SetShaderUniformFloatBrick: THREED_UNIFORM_NAME, VALUE_X
SetShaderUniformVec3Brick: THREED_UNIFORM_NAME, VALUE_X, VALUE_Y, VALUE_Z
SetShadowQualityBrick: SHADOW_SIZE, SHADOW_RESOLUTION
SetShadowsBrick: TEXT
SetSizeToBrick: SIZE
SetSkyColorBrick: VALUE_1, VALUE_2, VALUE_3
SetSkyboxBrick: FILENAME
SetSoundInstancePitchBrick: NAME, PITCH
SetSoundInstanceVolumeBrick: NAME, VOLUME
SetSoundVolumeBrick: VOLUME
SetSpawnInvisibleBrick: STRING
SetSpotLightBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5, VALUE_6, VALUE_7, VALUE_8, VALUE_9, VALUE_10, VALUE_11, VALUE_12, VALUE_13, VALUE_14
SetStopSoundsBrick: VALUE
SetTempoBrick: TEMPO
SetTextBrick: X_DESTINATION, Y_DESTINATION, STRING
SetTextBufferOnlyBrick: VALUE_1, VALUE_2
SetTextPropertyBrick: NAME, VALUE
SetTextureTilingBrick: OBJECT_ID, X, Y
SetThirdPersonCameraBrick: OBJECT_ID, DISTANCE, HEIGHT, PITCH
SetThreadColorBrick: THREAD_COLOR
SetTransparencyBrick: TRANSPARENCY
SetVariableBrick: VARIABLE
SetVariableEasingBrick: IF_CONDITION, INSERT_ITEM_INTO_USERLIST_VALUE, REPLACE_ITEM_IN_USERLIST_VALUE, INSERT_ITEM_INTO_USERLIST_INDEX
SetVelocityBrick: PHYSICS_VELOCITY_X, PHYSICS_VELOCITY_Y
SetViewPositionBrick: VIEW_ID, X_POSITION, Y_POSITION
SetVolumeToBrick: VOLUME
SetWebBrick: NAME
SetWidthBrick: SIZE
SetXBrick: X_POSITION
SetYBrick: Y_POSITION
ShaderBrick: VERTEX, FRAGMENT
ShareBrick: VALUE_1
ShowDialogBrick: NAME
ShowNotificationBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4, VALUE_5
ShowText3Brick: TEXT, NAME, X_POSITION, Y_POSITION, SIZE, COLOR
ShowTextBrick: X_POSITION, Y_POSITION
ShowTextColorSizeAlignmentBrick: X_POSITION, Y_POSITION, SIZE, COLOR
ShowTextFontBrick: TEXT, NAME, FILE, X_POSITION, Y_POSITION, SIZE, COLOR
ShowTextRotationBrick: TEXT, NAME, FILE, X_POSITION, Y_POSITION, SIZE, COLOR, VALUE
ShowVarFontBrick: X_POSITION, Y_POSITION, SIZE, COLOR, FILE
SignApkBrick: TEXT_1, TEXT_2, TEXT_3, TEXT_4, TEXT_5
SoundFileBrick: FILE
SoundFilesBrick: FILE
SpawnParticleInstanceBrick: FILE, NAME, X, Y
SpawnThreadBrick: IF_CONDITION
SpeakAndWaitBrick: SPEAK
SpeakBrick: SPEAK
SplitBrick: TEXT, VALUE
SquareBrick: X_POSITION, Y_POSITION, WIDTH, HEIGHT, NAME, COLOR, TRANSPARENCY, ROTATION, BORDERS
StartBufferRecordingBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
StartServerBrick: PORT
StopAnimationBrick: VALUE_1
StopParticleInstanceBrick: NAME
StopRecordingBrick: FILE_NAME
StopThreadBrick: IF_CONDITION
StoreCSVIntoUserListBrick: STORE_CSV_INTO_USERLIST_COLUMN, STORE_CSV_INTO_USERLIST_CSV
StringToTableBrick: STRING, X_POSITION, Y_POSITION, TABLE_NAME
TableToFloatBrick: TABLE_NAME, FLOAT_ARRAY
TapAtBrick: X_POSITION, Y_POSITION
TapForBrick: X_POSITION, Y_POSITION, DURATION_IN_SECONDS
ThinkBubbleBrick: STRING
ThinkForBubbleBrick: STRING, DURATION_IN_SECONDS
ThreedAlignNormalBrick: VALUE_1, VALUE_2, VALUE_3, VALUE_4
ThreedAttachObjectToBoneBrick: VALUE_1, VALUE_2, VALUE_3, X, Y, Z
ThreedBindBoneToObjectBrick: VALUE_1, VALUE_2, VALUE_3
ThreedCreateCylinderBrick: VALUE_1
ThreedCreateFixedConstraintBrick: VALUE_1, VALUE_2, VALUE_3, X, Y, Z, VALUE_4, VALUE_5, VALUE_6
ToggleDisplayBrick: VALUE
TouchAndSlideBrick: X_POSITION, Y_POSITION, X_POSITION_CHANGE, Y_POSITION_CHANGE, DURATION_IN_SECONDS
TripleStitchBrick: EMBROIDERY_LENGTH
TurnLeftBrick: TURN_LEFT_DEGREES
TurnLeftSpeedBrick: PHYSICS_TURN_LEFT_SPEED
TurnRightBrick: TURN_RIGHT_DEGREES
TurnRightSpeedBrick: PHYSICS_TURN_RIGHT_SPEED
UnzipBrick: FILE
UnzipProjectFilesBrick: VALUE_1
UpdateManifestBrick: TEXT_1, TEXT_2, TEXT_3, TEXT_4, TEXT_5, TEXT_6, TEXT_7, TEXT_8, TEXT_9, TEXT_10
UploadFileBrick: URL, FILE, TEXT
VibrationBrick: VIBRATE_DURATION_IN_SECONDS
VmRelativeMouseMoveBrick: X_POSITION, Y_POSITION, MASK
VmSetMonitorSizeBrick: WIDTH, HEIGHT
VoxelBuildBrick: NAME, TEXT, X, Y
VoxelConfigBrick: NAME, X, Y, Z
VoxelCreateWorldBrick: NAME, X, Y, Z, X_1, Y_1, Z_1
VoxelDeleteBrick: NAME
VoxelLoadStringBrick: NAME, TEXT, X, Y, Z
VoxelSetBlockBrick: NAME, X, Y, Z, VALUE, DATA
VoxelSetTransparentBrick: VALUE, VALUE_1
WaitBrick: TIME_TO_WAIT_IN_SECONDS
WaitThreadBrick: IF_CONDITION
WaitUntilBrick: IF_CONDITION
WebRequestBrick: WEB_REQUEST
WhenClonedWithNameBrick: VALUE_1
WhenConditionBrick: IF_CONDITION
WhenMqttMessageBrick: VALUE_1
WhenNotificationActionTriggeredBrick: VALUE_1
WhenNotificationClickedBrick: VALUE_1
WriteBaseBrick: FIREBASE_ID, FIREBASE_KEY, FIREBASE_VALUE
WriteToFilesBrick: VALUE
WriteVariableToFileBrick: WRITE_FILENAME
ZigZagStitchBrick: ZIGZAG_EMBROIDERY_LENGTH, ZIGZAG_EMBROIDERY_WIDTH
ZipBrick: FILE, TEXT
ZipProjectFilesBrick: VALUE_1, VALUE_2
```

### 6.21. Поля блоков, не являющиеся формулами (`bricks_data_fields.txt`)

Источник: выгрузка (852 строки) всех нестатических и нетранзиентных полей экземпляра в каталоге `content/bricks`. XStream записывает такие поля в XML, по умолчанию давая тегу имя поля. Раздел дополняет 6.20: там формульные параметры (`formulaList`), здесь всё остальное.

**Ограничения выгрузки (важно при разборе)**
- Поля 39 Kotlin-классов в этой выгрузке отсутствуют (шаблон требовал `;`); они получены отдельной выгрузкой и описаны ниже в подразделе «Блоки на Kotlin».
- Аннотации XStream в этой выгрузке не видны, но отдельная выгрузка по всему проекту показала, что у блоков их почти нет (подробнее в 6.22): переименованы только поля `FormulaBrick.formulaMap` (`formulaList`) и три поля `UserDefinedBrick`, а из XML исключено поле `ParameterizedBrick.parameterizedData`. У остальных блоков имя тега равно имени поля.
- Поля вложенных классов и поля типов интерфейса (`View`, `LinearLayout`, `Spinner` и т. п.) исключены.
- Значения по умолчанию взяты из инициализаторов полей; реальные значения в файле проекта могут быть другими.

**Общие поля всех блоков** (абстрактный `BrickBaseType`): `commentedOut` (`boolean`, по умолчанию `false`) и `brickId` (`UUID`, при создании блока генерируется случайный). Это теги `<commentedOut>` и `<brickId>` внутри `<brick>`.

**Составные блоки.** Вложенные блоки хранятся в полях-списках блока-контейнера (`List<Brick>`):

| Блок | Поля-списки |
|---|---|
| `AsyncRepeatBrick` | `loopBricks` (`List<Brick>`) |
| `ForItemInUserListBrick` | `loopBricks` (`List<Brick>`) |
| `ForVariableFromToBrick` | `loopBricks` (`List<Brick>`) |
| `ForeverBrick` | `loopBricks` (`List<Brick>`) |
| `IfLogicBeginBrick` | `ifBranchBricks` (`List<Brick>`), `elseIfBranches` (`List<ElseIfBranch>`), `elseBranchBricks` (`List<Brick>`) |
| `IfThenLogicBeginBrick` | `ifBranchBricks` (`List<Brick>`) |
| `InstantBrick` | `nestedBricks` (`List<Brick>`) |
| `IntervalRepeatBrick` | `loopBricks` (`List<Brick>`) |
| `PhiroIfLogicBeginBrick` | `ifBranchBricks` (`List<Brick>`), `elseBranchBricks` (`List<Brick>`) |
| `RepeatBrick` | `loopBricks` (`List<Brick>`) |
| `RepeatUntilBrick` | `loopBricks` (`List<Brick>`) |
| `RunAsSpriteBrick` | `nestedBricks` (`List<Brick>`) |
| `SpawnThreadBrick` | `threadBricks` (`List<Brick>`) |
| `TryCatchFinallyBrick` | `tryBricks` (`List<Brick>`), `catchBricks` (`List<Brick>`), `finallyBricks` (`List<Brick>`) |

`RaspiIfLogicBeginBrick` наследует поля `IfLogicBeginBrick`. **Версия:** по сообщению пользователя, неограниченная цепочка «иначе если» (поле `elseIfBranches` с `ElseIfBranch`) это новая возможность версии NewCatroid 2.3.0; в файлах 2.2.0 тега `elseIfBranches` нет (7.2, 7.3). Присланный исходник уже содержит это поле и класс, то есть он, по-видимому, новее релиза 2.2.0 и включает часть 2.3.0. Вспомогательный класс `ElseIfBranch` (не блок) содержит `condition` (`Formula`) и `branchBricks` (`List<Brick>`) и описывает одну ветку «иначе если». Классы `IfLogicElseBrick`, `IfLogicEndBrick`, `IfThenLogicEndBrick`, `LoopEndBrick` в каталоге есть (у них нет полей данных); попадают ли они в XML при такой структуре, по выгрузке не определить. Теги внутри списков, судя по `brickList` из 6.3, должны выглядеть как `<brick type="…">`, но для составных блоков этого в примерах не было.

**Блоки-шапки скриптов и их скрипты.** Каждый блок-шапка хранит свой скрипт в поле; это даёт соответствие «блок → класс скрипта» (см. 6.11):

| Блок-шапка | Поле | Класс скрипта |
|---|---|---|
| `BroadcastReceiverBrick` | `broadcastScript` | `BroadcastScript` |
| `BroadcastWithParamsReceiverBrick` | `script` | `BroadcastWithParamsReceiverScript` |
| `EmptyEventBrick` | `script` | `EmptyScript` |
| `UserDefinedReceiverBrick` | `userDefinedScript` | `UserDefinedScript` |
| `WhenAfterUpdateBrick` | `script` | `AfterUpdateScript` |
| `WhenAppMinimizedBrick` | `script` | `WhenAppMinimizedScript` |
| `WhenAppRestoredBrick` | `script` | `WhenAppRestoredScript` |
| `WhenBackPressedBrick` | `script` | `BackPressedScript` |
| `WhenBackgroundChangesBrick` | `script` | `WhenBackgroundChangesScript` |
| `WhenBeforeUpdateBrick` | `script` | `BeforeUpdateScript` |
| `WhenBounceOffBrick` | `script` | `WhenBounceOffScript` |
| `WhenBrick` | `script` | `WhenScript` |
| `WhenClonedBrick` | `script` | `WhenClonedScript` |
| `WhenClonedWithNameBrick` | `script` | `WhenClonedWithNameScript` |
| `WhenConditionBrick` | `script` | `WhenConditionScript` |
| `WhenFingerMovedOnScreenBrick` | `script` | `WhenFingerMovedOnScreenScript` |
| `WhenFingerMovedOverSpriteBrick` | `script` | `WhenFingerMovedOverSpriteScript` |
| `WhenGamepadButtonBrick` | `script` | `WhenGamepadButtonScript` |
| `WhenMouseButtonClickedBrick` | `script` | `WhenMouseButtonClickedScript` |
| `WhenMouseWheelScrolledBrick` | `script` | `WhenMouseWheelScrolledScript` |
| `WhenMqttMessageBrick` | `script` | `WhenMqttMessageScript` |
| `WhenNfcBrick` | `script` | `WhenNfcScript` |
| `WhenNotificationActionTriggeredBrick` | `script` | `WhenNotificationActionTriggeredScript` |
| `WhenNotificationClickedBrick` | `script` | `WhenNotificationClickedScript` |
| `WhenProjectExitsBrick` | `script` | `ExitProjectScript` |
| `WhenRaspiPinChangedBrick` | `script` | `RaspiInterruptScript` |
| `WhenSpriteReleasedBrick` | `script` | `WhenSpriteReleasedScript` |
| `WhenStartedBrick` | `script` | `StartScript` |
| `WhenTouchDownBrick` | `script` | `WhenTouchDownScript` |
| `WhenWindowResizedBrick` | `script` | `WhenWindowResizedScript` |

У `UserDefinedReceiverBrick` есть ещё поля `userDefinedBrick` (`Brick`) и `spinnerSelection` (`int`).

**Ссылки на объекты проекта и сцены**

| Блоки | Поле | Тип |
|---|---|---|
| `SetLookBrick`, `SetBackgroundBrick`, `SetHitboxBrick` | `look` | `LookData` |
| `PlaySoundBrick`, `PlaySoundAtBrick`, `SetSoundVolumeBrick` | `sound` | `SoundInfo` |
| `PointToBrick` | `pointedObject` | `Sprite` |
| `GoToBrick` | `destinationSprite` | `Sprite` |
| `CloneBrick`, `CloneAndNameBrick` | `objectToClone` | `Sprite` |
| `SceneStartBrick`, `ClearSceneBrick` | `sceneToStart` | `String` (имя сцены) |
| `SceneTransitionBrick` | `sceneForTransition` | `String` (имя сцены) |

Поля типов `LookData`, `SoundInfo`, `Sprite` указывают на объект проекта. XStream при повторном упоминании объекта обычно пишет `reference="…"` (так устроены `programVariableList` в 3.5 и 6.6); точный вид этих ссылок по присланным файлам не подтверждён. Сцены указываются именем (`String`).

Унаследованные поля (в самих классах их нет):
- `userVariable` (`UserVariable`) получают 36 блоков с базой `UserVariableBrick`, `UserVariableBrickWithFormula` или `UserVariableBrickWithVisualPlacement`: `AskBrick`, `AskGemini2Brick`, `AskGeminiBrick`, `AskSpeechBrick`, `BigAskBrick`, `BindVmOutputBrick`, `BroadcastWithParamsReceiverBrick`, `ChangeVariableBrick`, `CreateTextFieldBrick`, `ForVariableFromToBrick`, `GetZipFileNamesBrick`, `HideTextBrick`, `JavaCompileBrick`, `JavaDownloadDepBrick`, `ListenServerBrick`, `NativeViewListenerBrick`, `PostWebRequestBrick`, `PredictNNBrick`, `ReadBaseBrick`, `ReadFromFilesBrick`, `ReadVariableFromDeviceBrick`, `RunJSBrick`, `RunLuaBrick`, `RunShellBrick`, `SetCallbackBrick`, `SetVariableBrick`, `SetVariableEasingBrick`, `SetWebBrick`, `ShowText3Brick`, `ShowTextBrick`, `ShowTextColorSizeAlignmentBrick`, `ShowTextFontBrick`, `ShowTextRotationBrick`, `ShowVarFontBrick`, `WriteToFilesBrick`, `WriteVariableOnDeviceBrick`;
- `userList` (`UserList`) получают 10 блоков с базой `UserListBrick`: `AddItemToUserListBrick`, `ClearUserListBrick`, `DeleteItemOfUserListBrick`, `InsertItemIntoUserListBrick`, `ReadListFromDeviceBrick`, `RegexBrick`, `ReplaceItemInUserListBrick`, `SplitBrick`, `StoreCSVIntoUserListBrick`, `WriteListOnDeviceBrick`;
- `userDataList` (`UserDataHashMap`) получают блоки с базой `UserDataBrick`: `AssertUserListsBrick`, `ForItemInUserListBrick`;
- `broadcastMessage` (`String`) есть у блоков `BroadcastBrick`, `BroadcastWaitBrick`.

**Простые поля: выпадающие списки, флаги, строки** (67 блоков; формат `Блок: тип имя = значение по умолчанию; …`). Поля `…Selection`, `…Index`, `…Mode`, `spinnerSelection` хранят номер выбранного пункта выпадающего списка; что означает каждый номер, зависит от массива строк в ресурсах, которого в материалах нет. Поля `motor`, `tone`, `eye`, `ledStatus`, `animationName`, `soundName` это строки с именем выбранного варианта.

```
ApplyShaderBrick: int presetSelection = 0
BroadcastBrick: String broadcastMessage
ClearSceneBrick: String sceneToStart
ConfigureLightBrick: int configTypeSelection = 0
ConfigureMaterialBrick: int configTypeSelection = 0
ConfigureParticlesBrick: int configTypeSelection = 0
CreateImageViewBrick: int scaleSelection = 0
CreateScrollViewBrick: int scrollMode = 1; int overScrollMode = 1
CreateSpringConstraintBrick: boolean springX = false; boolean springY = true; boolean springZ = false
CreateTextLabelBrick: int formatMode = 0; int alignMode = 0; int scrollMode = 0
DronePlayLedAnimationBrick: String ledAnimationName = ""
Ease3DPropertyBrick: int propertySelectionIndex = 0; int typeSelectionIndex = 0
EasePropertyBrick: int propertySelectionIndex = 0; int typeSelectionIndex = 0
FlashBrick: int spinnerSelectionID
GoToBrick: int spinnerSelection
HttpConfigBrick: int configTypeSelection = 0
JavaDownloadDepBrick: boolean recursive = true
JumpingSumoAnimationsBrick: String animationName
JumpingSumoSoundBrick: String soundName
LegoEv3MotorMoveBrick: String motor
LegoEv3MotorStopBrick: String motor
LegoEv3MotorTurnAngleBrick: String motor
LegoEv3SetLedBrick: String ledStatus
LegoNxtMotorMoveBrick: String motor
LegoNxtMotorStopBrick: String motor
LegoNxtMotorTurnAngleBrick: String motor
NativeViewAnimateBrick: int propertySelection = 0; int easingSelection = 0
NativeViewConfigBrick: int propertySelection = 0
NativeViewControlBrick: int commandSelection = 0
NativeViewListenerBrick: int eventSelection = 0
NotificationAddButtonBrick: int behavior = 0; boolean hasInput = false; boolean autoClose = false
NotificationCreateBrick: int importanceSelection = 1; boolean isOngoing = false
PhiroIfLogicBeginBrick: int sensorSpinnerPosition = 0
PhiroMotorMoveBackwardBrick: String motor
PhiroMotorMoveForwardBrick: String motor
PhiroMotorStopBrick: String motor
PhiroPlayToneBrick: String tone
PhiroRGBLightBrick: String eye
PlayDrumForBeatsBrick: PickableDrum drumSelection = PickableDrum.values()[0]
PtOpBrick: int opSelection = 0
SceneStartBrick: String sceneToStart
SceneTransitionBrick: String sceneForTransition
SetActiveBrick: int activeStateSelection = 0
SetBufferShaderUniformBrick: int paramCount = 1
SetInstrumentBrick: PickableMusicalInstrument instrumentSelection = PickableMusicalInstrument.values()[0]
SetNfcTagBrick: int nfcTagNdefType = BrickValues.TNF_WELL_KNOWN_HTTPS
SetParticleBufferRenderBrick: int modeSelection = 0
SetParticlePropertyBrick: int propertySelection = 0
SetPenPropertyBrick: int propertySelection = 0
SetPhysicsObjectTypeBrick: PhysicsObject.Type type = PhysicsObject.Type.NONE
SetPostProcessingBrick: int effectIndex = 0; int paramIndex = 0
SetPostProcessingNewBrick: int effectIndex = 0; int paramIndex = 0
SetRotationLockBrick: boolean lockX = false; boolean lockY = false; boolean lockZ = false
SetRotationStyleBrick: int selection
SetTextPropertyBrick: int propertySelection = 0
SetVariableEasingBrick: int typeSelectionIndex = 0
ShowNotificationBrick: int importanceSelection = 1; boolean isOngoing = false
ShowText3Brick: int alignmentSelection = ALIGNMENT_STYLE_CENTERED
ShowTextColorSizeAlignmentBrick: int alignmentSelection = ALIGNMENT_STYLE_CENTERED
ShowTextFontBrick: int alignmentSelection = ALIGNMENT_STYLE_CENTERED
ShowTextRotationBrick: int alignmentSelection = ALIGNMENT_STYLE_CENTERED
ShowVarFontBrick: int alignmentSelection = ALIGNMENT_STYLE_CENTERED
StopScriptBrick: int spinnerSelection
UnknownBrick: String unknownClassName
UploadFileBrick: int fileTypeSelection = 0; int storageTypeSelection = 0
UserDefinedBrick: List<UserDefinedBrickData> userDefinedBrickDataList; UUID userDefinedBrickID; boolean isCallingBrick
UserDefinedReceiverBrick: Brick userDefinedBrick; int spinnerSelection
```

**Блоки на Kotlin** (поля из отдельной выгрузки; конструкторные `private var …` учтены как поля):

| Блок | Поля данных |
|---|---|
| `FadeParticleEffectBrick` | `fadeSpinnerSelectionId` (`Int` = `fadeType`) |
| `ParticleEffectAdditivityBrick` | `fadeSpinnerSelectionId` (`Int` = `fadeType`) |
| `NativeLayerBrick` | `spinnerSelectionON` (`Int` = `0`) |
| `CameraBrick` | `spinnerSelectionON` (`Boolean` = `true`) |
| `ChooseCameraBrick` | `spinnerSelectionFRONT` (`Boolean` = `true`) |
| `ChooseFileBrick` | `userVariable` (`UserVariable`), `fileTypeSelection` (`Int` = `0`) |
| `ReadVariableFromFileBrick` | `userVariable` (`UserVariable`), `spinnerSelectionID` (`Int` = `KEEP`) |
| `TouchAndSlideBrick` | `startCoordinates` (`Boolean` = `true`) |
| `StopSoundBrick` | `sound` (`SoundInfo?` = `null`) |
| `SetListeningLanguageBrick` | `languageObject` (`LanguageObject?` = `null`) |
| `AskGPTBrick` | `userVariable` (`UserVariable`) |
| `WebRequestBrick` | `userVariable` (`UserVariable`) |
| `WriteVariableToFileBrick` | `userVariable` (`UserVariable`) |
| `StartListeningBrick` | `userVariable` (`UserVariable`) |
| `ParameterizedEndBrick` | `userList` (`UserList`) |
| `CustomBrick` | `definitionId` (`String` = `""`), `parameterFormulas` (`MutableList<Formula>`); базовый класс в выгрузке не виден (объявление занимает несколько строк). Формулы хранятся списком по номеру параметра, а не в `formulaList`; описание блока берётся из `CustomBrickManager`, см. 6.23 |
| `ParameterizedBrick` (наследует абстрактный `ListSelectorBrick` с полем `userLists`: `MutableList<UserList>`) | `loopBricks` (`MutableList<Brick>`), `endBrick` (`ParameterizedEndBrick`), `parameterizedData` (`ParameterizedData`; **в XML не записывается**, помечено `@XStreamOmitField`) |

Вспомогательный класс `LanguageObject` (Kotlin `data class`, алиас `languageObject`): `languageName` (`String`), `languageTag` (`String`). Блоки Kotlin без собственных полей данных (18): `BackgroundRequestBrick`, `CopyLookBrick`, `DeleteLookBrick`, `EditLookBrick`, `LookRequestBrick`, `NextLookBrick`, `OpenUrlBrick`, `PaintNewLookBrick`, `PreviousLookBrick`, `SavePlotBrick`, `SetBackgroundByIndexAndWaitBrick`, `SetBackgroundByIndexBrick`, `SetCameraFocusPointBrick`, `SetParticleColorBrick`, `StartPlotBrick`, `StopPlotBrick`, `TapForBrick`, `WriteEmbroideryToFileBrick`. `SubCategoryHeaderBrick` (поля `title`, `templateBrick`, `isExpanded`, `isStacked` и графические) это заголовок подкатегории в палитре редактора, а не блок проекта; `EndBrick` хранит только идентификатор ресурса оформления (`viewResource`). Поля `lateinit var spinner` (тип `BrickSpinner`) исключены как элементы интерфейса.

**Особые поля**
- `UserDefinedBrick`: `userDefinedBrickDataList` (`List<UserDefinedBrickData>`), `userDefinedBrickID` (`UUID`), `isCallingBrick` (`boolean`; в реальном файле тег называется именно `isCallingBrick`, 7.1). Класс `UserDefinedBrickData` в выгрузку не входит.
- `UnknownBrick`: `unknownClassName` (`String`). Похоже на заглушку для блока неизвестного класса, но связи с загрузчиком в присланных файлах нет.
- `PlayDrumForBeatsBrick.drumSelection` (`PickableDrum`) и `SetInstrumentBrick.instrumentSelection` (`PickableMusicalInstrument`) по умолчанию равны первому значению перечисления. У обоих типов поля `nameStringId` (`int`), `value` (`int`), `name` (`String`).
- `SetPhysicsObjectTypeBrick.type` (`PhysicsObject.Type`), по умолчанию `NONE`.

**Покрытие.** Всего 598 неабстрактных Java-блоков; хотя бы одно поле данных (своё или унаследованное) у 159. Остальные Java-блоки либо не имеют полей данных, либо хранят только формулы (6.20). Данные 39 Kotlin-классов описаны в подразделе «Блоки на Kotlin».

### 6.22. Аннотации XStream: алиасы, атрибуты, порядок (`xstream_annotations.txt`, `xstreamfieldkeyorder.txt`)

Источник: все аннотации `@XStream…` в `catroid/src/main/java/org/catrobat/catroid` и списки порядка полей. Правила сортировки и чтения описаны в 6.30, алиасы классов в 6.28.

| Класс | Что задано аннотациями |
|---|---|
| `Project` (`<program>`) | алиас класса `program`; порядок полей: `header`, `settings`, `scenes`, `programVariableList`, `programListOfLists`, `programMultiplayerVariableList`, `disableScientificNotation`; алиасы полей: `header` (поле `xmlHeader`), `settings`, `programVariableList` (поле `userVariables`), `programMultiplayerVariableList` (поле `multiplayerVariables`), `programListOfLists` (поле `userLists`), `scenes` (поле `sceneList`), `disableScientificNotation`; класс помечен `@LunoClass` |
| `XmlHeader` | алиасы семи полей: `screenWidth`, `screenHeight`, `physicsWidthArea`, `physicsHeightArea`, `gitRemoteUrl`, `remixOf`, `url` (6.26); порядка полей нет (теги по алфавиту) |
| `Setting` | алиас класса `setting` |
| `Scene` | алиас `scene`; порядок полей: `sceneId` (**атрибут**), `name`, `objectList` (поле `spriteList`); класс помечен `@LunoClass` |
| `Sprite` (`<object>`) | порядок полей: `spriteId`, `name` (оба **атрибуты**), `lookList`, `soundList`, `scriptList`, `nfcTagList`, `userVariables`, `userLists`, `userDefinedBrickList`; класс помечен `@LunoClass`; атрибут `type` добавляет конвертер |
| `Script` | атрибуты `posX`, `posY`; атрибут `type` добавляет конвертер |
| `LookData` (`<look>`) | атрибуты `lookId`, `name`, `fileName` |
| `SoundInfo` (`<sound>`) | атрибуты `soundId`, `name`, `fileName` |
| `FormulaBrick` | поле `formulaMap` пишется как тег `formulaList` |
| `UserDefinedBrick` | алиасы `userDefinedBrickDataList`, `userDefinedBrickID`; для поля `isCallingBrick` задан алиас `callingBrick`, но в реальном `code.xml` записан тег `<isCallingBrick>` (7.1): этот алиас на запись не влияет |
| `UserDefinedBrickLabel`, `UserDefinedBrickInput` | алиасы классов `userDefinedBrickLabel`, `userDefinedBrickInput`; алиасы полей `label`, `input` |
| `CustomBrick`, `RunAsSpriteBrick` | алиас класса, равный имени класса |
| `LanguageObject` | алиас `languageObject`; порядок: `languageName`, `languageTag` |
| `ParameterizedBrick` | `@XStreamOmitField` на `parameterizedData`: поле в XML не пишется |

Дополнительно:
- Единственное поле, исключённое аннотацией, это `ParameterizedBrick.parameterizedData`; прочие исключения делаются ключевым словом `transient` (в выгрузки полей эти поля не попали).
- `@XStreamFieldKeyOrder` стоит только у `Project`, `Scene`, `Sprite`, `LanguageObject` и устаревших `SceneUntilLanguageVersion0999`; у остальных классов порядок определяется правилом из 6.30.
- Алиасы старых форматов (`ProjectUntilLanguageVersion0999`, `LegacyProjectWithoutScenes`, `LegacyDataContainer` с полями `programVariableList`, `programListOfLists`, `objectVariableList`, `objectListOfList`, `ProjectMetaDataParser`) относятся к чтению проектов до версии языка 0.999 (6.12).


### 6.23. Библиотеки `.newlib`, пользовательские блоки и формулы (`LibraryManager`, `CustomBrickManager`, `CustomBrickDefinition`)

Пользовательские блоки (`CustomBrick`) и пользовательские формулы (значения `FUNCTION`, которых нет в перечислении `Functions`, см. 6.13) определяются **библиотеками**. Библиотека это файл `*.newlib` в каталоге `project.libsDir` проекта (вероятно, `libs` в корне проекта, см. ниже). В `code.xml` лежат только ссылки на определения (`definitionId` у блока, имя функции в узле формулы).

**Формат `.newlib`.** ZIP-архив со следующими файлами:

| Файл внутри | Обязателен | Назначение |
|---|---|---|
| `code.txt` | да (без него загрузка падает с ошибкой «В библиотеке отсутствует code.txt») | исходный код на LunoScript |
| `formulas.xml` | нет | определения пользовательских формул |
| `bricks.xml` | нет | определения пользовательских блоков |

**`formulas.xml`.** Настоящий файл (из реального проекта, 7.2):
```xml
<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<formulas>
  <formula id="29481" function="sum" displayName="Сумма">
    <params>
      <param type="NUMBER" default="4" />
      <param type="NUMBER" default="7" />
    </params>
  </formula>
</formulas>
```
Загрузчик, судя по коду, ищет теги `formula` и `param` и корневой элемент не проверяет, но реальные файлы используют оболочку `<formulas>` и `<params>`.
- `id` — уникальное имя формулы (`uniqueName`); оно же значение `<value>` узла `FUNCTION` в `code.xml` (поиск по уникальному имени, см. 6.13).
- `function` — имя вызываемой функции LunoScript, `displayName` — название в редакторе.
- Каждый `param` задаёт один параметр: `type` одно из `STRING`, `NUMBER`, `USER_VARIABLE`, `USER_LIST` (регистр не важен; другое значение или отсутствие трактуется как `STRING`), `default` — значение по умолчанию (если нет, пустая строка). Число параметров равно числу тегов `param`.
- Формула без `id`, `function` или `displayName` пропускается.

**`bricks.xml`** (настоящий файл из реального проекта, 7.2):
```xml
<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<bricks>
  <brick id="5391938" function="toast" header="Тост {0} {о}">
    <params />
  </brick>
</bricks>
```
Для блока с параметрами внутри `<params>` лежат элементы `<param type="TEXT_FIELD" name="имя_параметра_в_Luno"/>`.
- `id` это значение `definitionId` у блока `CustomBrick` в `code.xml`; `function` — имя функции LunoScript; `header` — заголовок блока с метками параметров `{0}`, `{1}`. Блок без любого из этих трёх атрибутов пропускается.
- У `param` обязателен `name` (без него параметр пропускается). Атрибут `type` читается, но сейчас **любое значение превращается в `TEXT_FIELD`**: варианты `VARIABLE_DROPDOWN` и `LIST_DROPDOWN` есть в перечислении `ParameterType`, но их разбор закомментирован.
- Результат разбора: `CustomBrickDefinition(id, headerText, parameters, lunoFunctionName, ownerLibraryId)`, где `parameters` это список `BrickParameter(type: ParameterType, nameInLuno: String)`.

**Идентификатор библиотеки** это имя её файла (например, `mylib.newlib`). Оно записывается в `ownerLibraryId` всех формул и блоков библиотеки.

**Как библиотеки загружаются** (`LibraryManager.syncAndLoadLibraries(project)`):
1. Создаётся `project.libsDir`, если его нет; собираются файлы `*.newlib`.
2. Библиотеки, файлов которых больше нет, выгружаются: удаляются их формулы и блоки.
3. Новые библиотеки загружаются; уже загруженные повторно не читаются (проверки изменения файла нет).
4. Для каждой читаются `code.txt`, `formulas.xml`, `bricks.xml`. Для кода создаётся **свой** `Interpreter` LunoScript (область видимости строится на первом объекте основной сцены, `project.defaultScene.spriteList[0]`, значит, в проекте должна быть основная сцена хотя бы с одним объектом), код выполняется, затем регистрируются формулы (`CustomFormulaManager`) и блоки (`CustomBrickManager`).
5. Ошибка при загрузке библиотеки (нет `code.txt`, ошибка в коде и т. д.) отменяет регистрацию этой библиотеки, показывается уведомление, растёт счётчик ошибок. Ошибка разбора только `formulas.xml` или только `bricks.xml` логируется и не отменяет остальное; определения из повреждённого файла в этом случае не регистрируются.
6. Вызов `syncAndLoadLibraries` найден в `ProjectActivity` (при загрузке проекта в редакторе) и в `ProjectLibsFragment` (после выбора файла `.newlib`); других вызовов в `src/main/java` нет (6.29).

**`CustomBrickManager`** (Kotlin `object`): хранит определения блоков в памяти (`definitions`, ключ — `id`); `registerBrick` добавляет определение (повторная регистрация того же `id` перезаписывает его с предупреждением в логе); `removeBricksByOwner(libraryId)` удаляет все определения библиотеки; `findDefinitionById(id)` возвращает определение или `null`.

**Блок `CustomBrick` в `code.xml`** хранит `definitionId` и `parameterFormulas` (см. 6.21). Заголовок делится по шаблону `\{\d+\}`; судя по тому, что `CustomBrick.kt` берёт формулу из `parameterFormulas[index]` при обходе частей заголовка, номер метки, по-видимому, соответствует индексу параметра (точное правило в присланных строках не показано).

**Каталог `libs` и связанный код** (по выгрузке упоминаний `libsDir` и `.newlib`)
- `ApkBuilder` при сборке APK берёт все файлы `.jar` из каталога `<проект>/libs`; `DependencyManager` создаёт `<проект>/libs` и скачивает туда `.jar`-файлы; `DownloadDependencyAction` (блок `JavaDownloadDepBrick`, см. 6.5) читает список `.jar` из того же каталога. То есть `libs` в корне проекта уже используется для Java-зависимостей.
- `project.libsDir` это `Project.getLibsDir()` = `<проект>/libs` (`Project.java`, каталог создаётся при обращении); именно в нём лежат `.newlib`, а также `.jar` (6.25). Функция LunoScript `ProjectGetLibsDir` (один аргумент) в `Interpreter.kt` возвращает путь `proj.libsDir` как строку.
- Интерфейс: `ProjectLibsFragment` предлагает выбрать файл `.newlib` («Выберите файл .newlib»), `NewlibImporter` импортирует его (при ошибке пишет `Failed to import .newlib file`), `LibraryEditorActivity` экспортирует черновик библиотеки как `<имя>.newlib`. То есть в приложении есть встроенный редактор библиотек.
- Упаковка проекта в `.newtrobat` описана в 6.25: при экспорте через `ProjectExportTask` в архив попадает всё содержимое каталога проекта, включая `libs/`.

**Следствия для проекта**
- Библиотеки лежат в `project.libsDir`, то есть в каталоге проекта, а не в приложении глобально; значит, пользовательские блоки и формулы переносятся вместе с проектом, если архивируется весь каталог проекта. Каталог называется `libs` (6.25) и входит в архив при экспорте через `ProjectExportTask`.
- Если нужной библиотеки нет (файл удалён, не загружена, ошибка при загрузке), её определения не зарегистрированы, и вызов пользовательской формулы возвращает `0`; строки `LIB NOT FOUND` и `FUNC NOT FOUND` возвращаются, только когда определение есть, но библиотека не загружена или в ней нет нужной функции (6.27). `CustomBrick` без определения остаётся; что он делает в этом случае, по присланным файлам неизвестно.
- Определения блоков и формул не входят в `code.xml`, поэтому по `code.xml` одному нельзя узнать, что делает `CustomBrick` или пользовательская формула.

### 6.24. Расширение, имена файлов и каталоги проекта (`Constants`, `LaunchProjectAction`, манифест и др.)

Источник: выгрузка `libs_refs2.txt` (строки с `libsDir` и `newtrobat` без учёта регистра по `catroid/src/main`). Выгрузка показывает только строки с совпадением, поэтому там, где нужен контекст, сказано, чего не видно.

**Расширение и распознавание архива**
- `Constants.CATROBAT_EXTENSION = ".newtrobat"` (`Constants.java`, строка 69): константа названа по-старому, значение `.newtrobat`.
- `LaunchProjectAction` считает файл ZIP-архивом, если его имя оканчивается на `.zip` или `.newtrobat` (без учёта регистра). Это подтверждает, что `.newtrobat` это обычный ZIP. Блок `LaunchProjectBrick` в палитре подставляет по умолчанию имя `project.newtrobat`.
- Сообщение выбора файла «Выберите файл .newtrobat или .catrobat» говорит, что принимается и прежнее расширение `.catrobat`.
- В `AndroidManifest.xml` есть шаблон открытия файлов `.*\\.catrobat\\.newtrobat` (двойное расширение). Другие шаблоны манифеста в выгрузку не вошли, так как не содержат слова `newtrobat`.

**Имена файлов при обмене**
- `ProjectOptionsFragment` формирует параметр `file_name` со значением `<имя проекта>.newtrobat`; куда уходит этот параметр, по одной строке не видно.
- `CommunityWebViewActivity` считает ссылки, содержащие `.newtrobat`, загружаемыми проектами и берёт часть имени между последним `_` и `.newtrobat` (вероятно, идентификатор проекта на сайте).

**Каталоги внутри каталога проекта и кто их использует**

| Каталог | Для чего (по коду) |
|---|---|
| `libs/` | `.jar`-зависимости: их скачивает `DependencyManager`, читают `ApkBuilder`, `CompileJavaToDexAction`, `DownloadDependencyAction`; библиотеки `.newlib` хранятся в `project.libsDir` (6.23) |
| `libs_processed/` | обработанные `.jar` для запуска скриптов и DEX (`ScriptExecutor`, `LoadAndRunDexAction`) |
| `jniLibs/` | нативные библиотеки, из которых `ApkBuilder` берёт файлы при сборке APK |

Экспорт через `ProjectExportTask` упаковывает все элементы каталога проекта (`projectDir.listFiles()`), поэтому эти каталоги входят в архив (6.25); второй путь экспорта, `zipProjectWithoutSaves`, пропускает только `DeviceVariables.json`, `DeviceLists.json` и `undo_code.xml` (6.29). Другие каталоги из выгрузки (`default_pylibs`, `pylibs_unpacked/<имя файла>` в `filesDir` приложения, `native_libs_*` в кэше) лежат вне проекта и в архив не входят.

**Защита каталога библиотек**
- `Project.getLibsDir()` возвращает `<проект>/libs`; метод `getLib(имя)` строит файл в этом каталоге по «очищенному» имени (`\` заменяется на `/`) и бросает `SecurityException`, если канонический путь файла выходит за пределы каталога. Такая же защита есть у `getFile(имя)` для `files/` (6.25).
- `ProjectSecurityChecker.projectContainsDangerousBricks(project)` возвращает `true`, если (1) в каталоге `libs/` есть хотя бы один файл (любой: `.newlib`, `.jar`), либо (2) среди блоков, лежащих **непосредственно в списке блоков** какого-либо скрипта, есть `LunoScriptBrick` или `RunPythonScriptBrick`. Несмотря на название метода `checkBrickRecursively`, вложенные блоки (внутри циклов, условий) он не обходит, так что такие блоки проверка не обнаружит. Что приложение делает с результатом и вызывается ли проверка при открытии `.newtrobat`, по выгрузке не видно.

### 6.25. Файлы и каталоги проекта, упаковка (`Constants`, `Project`, `ProjectExportTask`, `ZipArchiver` и др.)

Источник: разделы `CONSTANTS`, `PACKAGING`, `PROJECT_LIBS` выгрузки `batch1.txt`.

**Имена файлов, каталогов и расширений (`Constants.java`)**

| Константа | Значение | Смысл |
|---|---|---|
| `CODE_XML_FILE_NAME` | `code.xml` | главный файл проекта |
| `PERMISSIONS_FILE_NAME` | `permissions.txt` | устаревший файл: при загрузке проектов версии не выше 0.99992 он удаляется (6.33) |
| `TMP_CODE_XML_FILE_NAME`, `UNDO_CODE_XML_FILE_NAME` | `tmp_code.xml`, `undo_code.xml` | по именам, временные версии `code.xml` (при сохранении и отмене) |
| `SCREENSHOT_AUTOMATIC_FILE_NAME`, `SCREENSHOT_MANUAL_FILE_NAME` | `automatic_screenshot.png`, `manual_screenshot.png` | снимки экрана: `automatic_screenshot.png` бывает и в корне проекта, и в каталоге каждой сцены; `manual_screenshot.png` (если задан) лежит в корне (7.1, 7.2) |
| `NO_MEDIA_FILE` | `.nomedia` | служебный файл, скрывающий каталог от галереи |
| `IMAGE_DIRECTORY_NAME`, `SOUND_DIRECTORY_NAME` | `images`, `sounds` | каталоги изображений и звуков (внутри каталога сцены) |
| `CATROBAT_EXTENSION` | `.newtrobat` | расширение архива проекта |
| `NEW_CATROBAT_EXTENSION` | `.catrobat` | прежнее расширение Catrobat (имя константы перепутано) |
| `ZIP_EXTENSION`, `APK_EXTENSION` | `.zip`, `.apk` | |
| `DEFAULT_IMAGE_EXTENSION`, `JPEG_IMAGE_EXTENSION` | `.png`, `.jpg` | расширения изображений по умолчанию |
| `DEFAULT_SOUND_EXTENSION` | `.wav` | расширение звука по умолчанию |
| `EMBROIDERY_FILE_EXTENSION`, `SVG_FILE_EXTENSION`, `TEXT_FILE_EXTENSION` | `.dst`, `.svg`, `.txt` | |

Каталоги `backpack`, `scenes` (рюкзак), `backpack_sound`, `backpack_image`, `recent_bricks`, а также кэш (`pocketPaint`, `camera`, `soundRecorder`, `mediaLibrary`, `tmp`), по названиям относятся к хранению приложения, а не к проекту.

**Каталоги проекта (`Project.java`)**
- `getFilesDir()` возвращает `<проект>/files` и создаёт каталог при обращении. Это папка `files/` из исходного описания структуры.
- `getLibsDir()` возвращает `<проект>/libs` и тоже создаёт его. Здесь лежат `.newlib` (6.23) и `.jar`-зависимости (6.24).
- `getFile(имя)` строит путь внутри `files/`: символы `\` заменяются на `/`, недостающие родительские каталоги создаются, а если канонический путь выходит за пределы `files/`, бросается `SecurityException`. Подкаталоги внутри `files/` допустимы. `getLib(имя)` работает так же для `libs/`.
- Поле `Project.directory` помечено `transient`: путь проекта в XML не записывается.

**Упаковка и распаковка**
- `ZipArchiver` (пакет `io`): `zip(файл, File[])` и `unzip(File | InputStream, каталог)`.
- **Экспорт.** `ProjectExportTask` вызывает `ZipArchiver().zip(cacheFile, projectDir.listFiles())`: в архив попадают **все элементы каталога проекта** (`code.xml`, каталоги сцен, `files/`, `libs/`, `libs_processed/`, `jniLibs/`, служебные файлы); судя по именам переменных (`cacheFile`, `projectDestination`), архив сначала собирается в кэше, затем передаётся в выбранное пользователем место. Имя по умолчанию `<имя проекта>.newtrobat`. Второй путь, `ProjectOptionsFragment.zipProjectWithoutSaves(dir, zos, basePath)`, рекурсивно упаковывает проект, пропуская только файлы `DeviceVariables.json`, `DeviceLists.json` и `undo_code.xml` (6.29).
- **Обмен с сервером.** Выгрузка идёт файлом `upload.newtrobat` (`ProjectUploadService`), скачивание файлом `down.newtrobat` с последующим `ZipArchiver().unzip(файл, каталог проекта)`.
- **Импорт.** `ProjectUnZipperAndImporter` распаковывает архив во временный каталог и импортирует проект. `ProjectListFragment` различает окончания `.newtrobat` и `.catrobat`; ветка `.catrobat` содержала проверку «новой структуры» архива, сейчас закомментированную. `CommunityWebViewActivity` читает имя проекта из `code.xml` распакованного каталога. Те же `ZipArchiver` или собственные распаковщики используют `LaunchProjectAction`, `MainMenuActivity`, `MatryoshkaManager`.
- **Объекты.** Расширение `.newtrobat` используется и при добавлении объекта-спрайта из файла (`ProjectActivity.addSpriteObjectFromUri(uri, CATROBAT_EXTENSION, true)`, `SpriteListFragment`); формат такого файла по выгрузке не виден.
- Блоки `UnzipProjectFilesBrick` и `UnzipBrick` распаковывают ZIP в рабочем проекте (поля `VALUE_1` и `FILE`, см. 6.20).

### 6.26. Поля основных классов модели (`batch1.txt`, раздел `MODEL_FIELDS`)

**Ограничение выгрузки:** в неё попали только объявления полей без вызова `(...)` в инициализаторе. Поля вида `= new ArrayList<>()` или `= UUID.randomUUID()` (например, `brickList` и `scriptId` у `Script`, `lookList`, `soundList`, `scriptList` у `Sprite`, `xmlHeader` у `Project`) здесь не видны. Тег XML равен имени поля, если не указан псевдоним.

**`XmlHeader`** (тег `<header>`; аннотации порядка полей у класса нет, поэтому порядок задаёт XStream по умолчанию)

| Поле Java | Тег в XML | Тип и значение по умолчанию |
|---|---|---|
| `programName`, `description`, `notesAndCredits` | то же | `String` |
| `virtualScreenWidth` | `screenWidth` | `int`, `0` |
| `virtualScreenHeight` | `screenHeight` | `int`, `0` |
| `physicsWidthArea` | `physicsWidthArea` | `float`, `3.0` |
| `physicsHeightArea` | `physicsHeightArea` | `float`, `2.0` |
| `screenMode` | то же | `ScreenModes`, `STRETCH` |
| `customResolution` | то же | `Boolean`, `false` |
| `catrobatLanguageVersion` | то же | `double` |
| `landscapeMode` | то же | `boolean` |
| `isCastProject` | то же | `boolean`, `false` |
| `scenesEnabled` | то же | `boolean`, `true` |
| `listeningLanguageTag` | то же | `String`, `""` |
| `applicationName`, `applicationVersion`, `applicationBuildName`, `applicationBuildType` | то же | `String`, `""` |
| `applicationBuildNumber` | то же | `int`, `0` |
| `deviceName`, `platform`, `platformVersion`, `tags` | то же | `String`, `""` |
| `gitRemoteUrl` | `gitRemoteUrl` | `String`, `""` |
| `remixGrandparentsUrlString` | `remixOf` | `String`, `""` |
| `remixParentsUrlString` | `url` | `String`, `""` |
| `userHandle`, `dateTimeUpload`, `mediaLicense`, `programLicense` | то же | `String`, `""` |

**Остальные классы**

| Класс | Поля, которые пишутся в XML | Не пишутся (`transient`) |
|---|---|---|
| `Project` | `header`, `settings`, `scenes`, `programVariableList`, `programMultiplayerVariableList`, `programListOfLists` (псевдонимы), `disableScientificNotation` (`boolean`, `false`) | `directory`, `variableCache`, `listCache` |
| `Scene` | `sceneId` (**атрибут**), `name`, `objectList` | `physicsWorld`, `project`, `firstStart` |
| `Sprite` | `spriteId` и `name` (**атрибуты**); списки `lookList`, `soundList`, `scriptList`, `nfcTagList`, `userVariables`, `userLists`, `userDefinedBrickList` (порядок из 6.22) | `isClone`, `myOriginal`, `runtimeName`, `variableCache`, `listCache` и другие рабочие поля |
| `Script` (абстрактный) | `commentedOut` (`boolean`, `false`, тег), `posX` и `posY` (`float`, **атрибуты**); скрипт-специфичные поля ниже | `scriptBrick` |
| `LookData` | `lookId`, `name`, `fileName` (**атрибуты**), `valid` (`boolean`, `true`), `isWebRequest` (`boolean`, `false`) | `file`, `thumbnailBitmap`, `width`, `height`, `pixmap`, `collisionInformation` |
| `SoundInfo` | `soundId`, `name`, `fileName` (**атрибуты**), `midiFile` (`boolean`, тег; в реальном файле `<midiFile>false</midiFile>`, 7.3) | `file` |
| `NfcTagData` | `name`, `uid` (`String`) | |
| `UserVariable` | `name`, `initialIndex` (`int`, `-1`), `deviceValueKey` (`UUID`) | `value`, `visible`, `dummy` |
| `UserList` | `name`, `initialIndex` (`int`, `-1`), `deviceListKey` (`UUID`) | `list` |
| `UserDefinedBrickInput` (алиас `userDefinedBrickInput`) | `input` (поле `name` типа `InputFormulaField`), `initialIndex` (`int`, `-1`) | `value` (`Formula`) |
| `UserDefinedBrickLabel` (алиас `userDefinedBrickLabel`) | `label` (`String`) | |

Следствия:
- **Значения переменных и списков в `code.xml` не записываются**: `UserVariable.value` и `UserList.list` помечены `transient`. В файле лежат имя, начальный индекс и ключ `deviceValueKey` / `deviceListKey`; сами значения хранятся вне `code.xml`, в файлах `DeviceVariables.json` и `DeviceLists.json` каталога проекта (формат `{ключ: значение}`, подтверждено на реальном проекте, 7.1).
- `UserDefinedBrickInput` и `UserDefinedBrickLabel` наследуют абстрактный `UserDefinedBrickData`. `InputFormulaField` реализует `Brick.FormulaField`, то есть ключ формулы пользовательского блока это не `BrickField`; поля самого `InputFormulaField` в выгрузку не попали.
- Атрибуты (а не вложенные теги): `sceneId`; `spriteId`, `name` у `Sprite`; `posX`, `posY` у `Script`; `lookId`, `name`, `fileName` у `LookData`; `soundId`, `name`, `fileName` у `SoundInfo`.

**Простые поля подклассов `Script`** (из выгрузки; поля с вызовами в инициализаторе не видны)

| Скрипт | Поля |
|---|---|
| `BroadcastScript` | `receivedMessage` (`String`) |
| `BroadcastWithParamsReceiverScript` | `userVariable` (`UserVariable`) |
| `RaspiInterruptScript` | `pin`, `eventValue` (`String`) |
| `UserDefinedScript` | `userDefinedBrickID` (`UUID`), `userDefinedBrickInputs` (`List<Object>`; в реальном файле это элементы `<userVariable>` с именами входов, 7.1), `screenRefresh` (`Boolean`, `true`) |
| `WhenBackgroundChangesScript` | `look` (`LookData`) |
| `WhenBounceOffScript` | `spriteToBounceOffName` (`String`, `""`); `spriteToBounceOff` не записывается |
| `WhenGamepadButtonScript` | `action` (`String`) |
| `WhenMouseButtonClickedScript` | `buttonCode` (`int`, код кнопки libGDX: левая, правая и т. д.) |
| `WhenNfcScript` | `nfcTag` (`NfcTagData`), `matchAll` (`boolean`, `true`) |

У остальных скриптов (`StartScript`, `WhenScript`, `WhenTouchDownScript`, `WhenClonedScript`, `WhenClonedWithNameScript`, `WhenConditionScript`, `WhenMqttMessageScript`, `WhenSpriteReleasedScript`, `WhenFingerMoved…Script`, `WhenNotification…Script`, `WhenAppMinimizedScript`, `WhenAppRestoredScript`, `WhenWindowResizedScript`, `WhenMouseWheelScrolledScript`, `BeforeUpdateScript`, `AfterUpdateScript`, `BackPressedScript`, `ExitProjectScript`, `EmptyScript`) простых полей нет; формулы и другие поля с инициализаторами-вызовами в выгрузку не попали.

### 6.27. Функции формул: аргументы и результат (`FormulaElement.java`)

Таблицы описывают, что делает каждое значение `FUNCTION` при вычислении (метод `interpretFunction`): 146 функций разобраны в `switch` внутри `FormulaElement`, `RAND` и `IF_THEN_ELSE` обрабатываются отдельно, ещё 36 вычисляются провайдерами; их код разобран ниже, кроме тел двух функций детектора объектов (класс найден, но тела в выгрузке нет) и функции `CLIPBOARD_TEXT`. Позиции аргументов: 1-й это `leftChild`, 2-й `rightChild`, 3-й и 4-й `additionalChildren[0]` и `[1]` (6.13). Правила приведения типов те же, что в 6.13.

**Общие соглашения (видны по коду)**
- Текстовые аргументы берутся как `String.valueOf(арг)`; числовые параметры, которые должны быть целыми, читаются безопасно: не число → «нет значения».
- Логический результат это число `1` (истина) или `0` (ложь).
- Если нужный менеджер недоступен (нет 3D-менеджера, нет запущенной сцены, нет активного окна сцены), функции доступа к объектам возвращают нейтральное значение: `0`, `""`, `0` или `-1` (указано ниже).
- Идентификаторы объектов, лучей, таблиц, представлений, тензоров это строки, заданные в соответствующих блоках.

**Строки**

| Функция | Аргументы | Результат |
|---|---|---|
| `LENGTH` | значение | длина: для константы число или строка это длина записи; для переменной длина её значения как текста; для списка длина текстового представления; `NaN` даёт `0` |
| `LETTER` | номер, текст | символ с указанным номером (с 1); вне диапазона или номер не число: `""` |
| `SUBTEXT` | с, по, текст | подстрока с символа `с` по `по` включительно (с 1); при некорректных границах `""` |
| `UPPER`, `LOWER`, `REVERSE` | текст | верхний регистр, нижний регистр, обратный порядок |
| `REPEAT` | текст, раз | текст, повторённый `раз` раз (не число: 0 раз, то есть `""`) |
| `REPLACE` | текст, что, чем | замена всех вхождений |
| `CONTAINS_STR` | текст, часть | `1`, если текст содержит часть |
| `JOIN`, `JOINNUMBER` | а, б | конкатенация (у обеих одинаково) |
| `JOIN3` | а, б, в | конкатенация трёх значений |
| `REGEX` | шаблон, текст | первое совпадение: группа 1, если в шаблоне есть группы, иначе всё совпадение; нет совпадения `""`; ошибка в шаблоне возвращает текст ошибки. Флаги `DOTALL` и `MULTILINE` |
| `RANDOM_STR` | длина | случайная строка латинских букв; длина не больше 0 или не число: `""` |
| `TO_HEX` | число | целое в шестнадцатеричной записи, заглавные буквы; не число: `"0"` |
| `TO_DEC` | hex-строка | целое число; ошибка разбора: `0` |
| `CHAR_TO_UNICODE` | символ | кодовая точка первого символа; пусто: `0` |
| `UNICODE_TO_CHAR` | код | символ по коду; принимает также записи `U+…` и `\u…`; пусто: `""` |
| `UNESCAPE_UTF` | текст | заменяет последовательности `\uXXXX` реальными символами |
| `DISTANCE` | строка1, строка2 | расстояние Левенштейна (число) |
| `MD5`, `SHA256` | текст | хеш строки в виде текста |
| `LUA` | код Lua | выполняет код Lua (LuaJ) и возвращает результат строкой; ошибка: `"0"`; скомпилированный код кэшируется по тексту |

**Математика и условие**

| Функция | Аргументы | Результат |
|---|---|---|
| `RAND` | от, до | случайное число между границами (порядок не важен); если обе границы целые константы без десятичной точки, результат целый |
| `IF_THEN_ELSE` | условие, если истина, если ложь | значение одной из веток; условие `NaN` даёт `NaN`; ветка-строка возвращается как есть, иначе число (нечисловое значение превращается в `0`) |
| `CLAMP` | значение, мин, макс | значение, ограниченное целыми границами; не число: `""` |
| `DISTAN` | x1, y1, x2, y2 | расстояние между двумя точками |
| `GET_DIRECTION_X` | угол (градусы) | косинус угла |
| `GET_DIRECTION_Y` | угол (градусы) | синус угла |
| `GET_ANGLE` | x, y | угол вектора (x, y) в градусах (`atan2(y, x)`) |
| `SIN`, `COS`, `TAN` | угол в градусах | синус, косинус, тангенс |
| `ARCSIN`, `ARCCOS`, `ARCTAN` | число | обратная функция, результат в градусах |
| `ARCTAN2` | a, b | `atan2(a, b)` в градусах; если оба аргумента `0`, возвращается случайный угол от -180 до 180 |
| `LN`, `LOG`, `EXP`, `SQRT`, `ABS` | число | натуральный логарифм, десятичный логарифм, экспонента, корень, модуль |
| `POWER` | основание, степень | возведение в степень |
| `MAX`, `MIN` | a, b | больший и меньший из двух |
| `ROUND` | число | округление до ближайшего целого (результат число с плавающей точкой) |
| `ROUNDTO` | число, знаков | округление до заданного числа знаков после запятой (отрицательное число знаков округляет влево) |
| `FLOOR`, `CEIL` | число | округление вниз и вверх |
| `MOD` | делимое, делитель | остаток со знаком делителя; если делимое или делитель равны `0`, возвращается делимое |
| `PI` | нет | число π |
| `TRUE`, `FALSE` | нет | `1` и `0` |

**Списки** (первый или второй аргумент это узел `USER_LIST`)

| Функция | Аргументы | Результат |
|---|---|---|
| `LIST_ITEM` | номер, список | элемент с номером (с 1); вне диапазона или не число: `""` |
| `NUMBER_OF_ITEMS` | список | число элементов; если передан не список, как `LENGTH` |
| `CONTAINS` | список, значение | `1`, если есть равный элемент |
| `INDEX_OF_ITEM` | значение, список | номер первого равного элемента (с 1) или `0` |
| `FIND` | список, значение | номер (с 1) первого элемента, равного по тексту, иначе `""` |
| `CONNECT` | список, разделитель | все элементы через разделитель (разделитель добавляется и после последнего) |
| `FLATTEN` | список | текстовое «разворачивание» списка (формат в присланных строках не показан) |

**Переменные, таблицы, массивы, JSON**

| Функция | Аргументы | Результат |
|---|---|---|
| `VAR` | имя | значение переменной по имени через `UserVarsManager` |
| `VARNAME` | номер | имя переменной по номеру; номер не число: используется `-1` |
| `VARVALUE` | номер | значение переменной по номеру; номер не число: используется `-1` |
| `TABLE_X`, `TABLE_Y` | имя таблицы | размер таблицы по X и по Y |
| `TABLE_ELEMENT` | имя, x, y | значение ячейки (индексы не числа: 0) |
| `TABLE_JOIN` | имя, разделитель, разделитель | таблица в виде строки (три текстовых аргумента) |
| `FLOATARRAY` | имя массива | размер массива чисел |
| `JSON_GET` | json, путь | значение по пути |
| `JSON_SET` | json, путь, значение | JSON с изменённым значением |
| `JSON_IS_VALID` | json | `1`, если строка корректный JSON |

**Файлы проекта** (имена относятся к каталогу `files/` проекта; `Project.getFile` не выпускает путь за пределы каталога, 6.25)

| Функция | Аргументы | Результат |
|---|---|---|
| `FILE` | имя | `1`, если файл существует, это файл и он читаем, иначе `0` |
| `FILES_PATH` | нет | **имена** файлов каталога `files/` (без подкаталогов), каждое с новой строки |
| `ALL_FILES` | нет | **абсолютный путь** каталога `files/` (имена функций `FILES_PATH` и `ALL_FILES` по смыслу перепутаны) |
| `FILE_SIZE` | имя | размер в байтах; нет файла: `0` |
| `READ_FILE` | имя | текст файла в UTF-8; нет файла `""`; больше 2 МБ: `"File is too large"` |
| `FILE_TO_BASE64` | имя | Base64 без переносов строк; нет файла или ошибка: `""` |
| `FILE_MD5`, `FILE_SHA256` | имя | хеш файла |
| `FILE_LAST_MODIFIED` | имя | время последнего изменения (число); нет файла: `0` |
| `IMAGE_WIDTH`, `IMAGE_HEIGHT` | имя | размеры изображения; нет файла: `0` |
| `MEDIA_DURATION` | имя | длительность медиафайла; нет файла: `0` |

**Сеть, MQTT, уведомления, буфер обмена**

| Функция | Аргументы | Результат |
|---|---|---|
| `HTTP_RESPONSE_TEXT` | id запроса | текст ответа |
| `HTTP_RESPONSE_CODE` | id запроса | код ответа (число) |
| `HTTP_RESPONSE_HEADER` | id, имя заголовка | значение заголовка |
| `MQTT_MESSAGE` | id комнаты | последнее полученное сообщение |
| `NOTIFICATION_REPLY` | id действия | сохранённый ответ пользователя из уведомления или `""` |
| `CLIPBOARD_TEXT` | нет | обработчика для функции не найдено; в редакторе используется одноимённый **датчик** `CLIPBOARD_TEXT` (`SensorHandler`) |

**Нативные View и видео** (окно сцены должно быть открыто, иначе `0`/`false`)

| Функция | Аргументы | Результат |
|---|---|---|
| `VIEW_X`, `VIEW_Y`, `VIEW_WIDTH`, `VIEW_HEIGHT` | id представления | положение и размер |
| `VIDEO_PLAYING` | id видео | `true`, если воспроизводится |
| `VIDEO_TIME` | id видео | текущее время воспроизведения |

**Касания, цвет, столкновения (2D)**

| Функция | Аргументы | Результат |
|---|---|---|
| `IS_MOUSE_BUTTON_DOWN` | код кнопки libGDX | `1`, если кнопка нажата; не число: `0` |
| `MULTI_FINGER_X`, `MULTI_FINGER_Y` | номер касания | координаты касания с этим номером |
| `MULTI_FINGER_TOUCHED` | номер касания | `1`, если этот палец касается экрана |
| `INDEX_CURRENT_TOUCH` | номер | индекс текущего касания по номеру (по `TouchUtil`) |
| `COLLIDES_WITH_COLOR` | цвет | `1`, если объект касается этого цвета |
| `COLOR_TOUCHES_COLOR` | цвет1, цвет2 | `1`, если цвет1 объекта касается цвета2 |
| `COLOR_AT_XY` | x, y | цвет в точке сцены |
| `COLOR_EQUALS_COLOR` | цвет1, цвет2, допуск | `1`, если цвета равны с допуском |
| `TOUCHES_OBJECT_BY_NAME` | имя объекта | `1`, если текущий объект касается объекта с таким именем; нет окна сцены: `0` |
| `RAY_DID_HIT2` | id луча | `1`, если 2D-луч (физический мир) попал |
| `RAY_HIT_SPRITE_NAME` | id луча | имя объекта, в который попал луч; нет: `""` |
| `RAY_HIT_X`, `RAY_HIT_Y`, `RAY_HIT_DISTANCE` | id луча | точка и расстояние попадания; нет данных: `0` |
| `CAMERA_X`, `CAMERA_Y`, `CAMERA_ROTATION`, `CAMERA_ZOOM` | нет | позиция, поворот и масштаб камеры сцены (по умолчанию `0`, `0`, `0`, `1`) |

**3D** (нужен 3D-менеджер, иначе нейтральное значение)

| Функция | Аргументы | Результат |
|---|---|---|
| `GET_3D_POSITION_X`, `_Y`, `_Z` | id объекта | компоненты позиции; нет объекта: `0` |
| `GET_3D_ROTATION_YAW`, `_PITCH`, `_ROLL` | id объекта | поворот: yaw это компонента `y`, pitch `x`, roll `z` |
| `GET_3D_SCALE_X`, `_Y`, `_Z` | id объекта | масштаб по осям |
| `GET_3D_VELOCITY_X`, `_Y`, `_Z` | id объекта | скорость по осям |
| `GET_3D_DISTANCE` | id1, id2 | расстояние между объектами; нет данных: `0` |
| `OBJECT_TOUCHES_OBJECT` | id1, id2 | `1`, если физически касаются |
| `OBJECT_INTERSECTS_OBJECT` | id1, id2 | `1`, если пересекаются |
| `COLLISION_LIST`, `INTERSECT_LIST` | id объекта | список физических столкновений и пересечений объекта |
| `DELTA` | нет | время кадра в виде строки; нет менеджера: `"-1"` |
| `GET_CAMERA_POS_X/Y/Z`, `GET_CAMERA_DIR_X/Y/Z`, `GET_CAMERA_ROTATION_YAW/PITCH/ROLL` | нет | позиция, направление, поворот 3D-камеры |
| `RAY_DID_HIT` | id луча | `1`, если 3D-луч попал |
| `GET_RAY_HIT_X/Y/Z`, `GET_RAY_HIT_NORMAL_X/Y/Z` | id луча | точка попадания и нормаль |
| `GET_RAY_DISTANCE` | id луча | расстояние до попадания; нет менеджера: `-1` |
| `GET_RAY_HIT_OBJECT` | id луча | id объекта, в который попал луч, или `""` |
| `VOXEL_GET_ID`, `VOXEL_GET_DATA` | мир, x, y, z | значение воксельного буфера по целым координатам (дробная часть отбрасывается вниз); нет мира: `0` |
| `ID_OF_DETECTED_OBJECT`, `OBJECT_WITH_ID_VISIBLE` | один числовой аргумент (в редакторе по умолчанию `1`) | реализует `ObjectDetectorFunctionProvider.kt`; требуют ресурс `OBJECT_DETECTION` (6.3); тело функций в выгрузку не попало |

**Fast2D и тензоры**

| Функция | Аргументы | Результат |
|---|---|---|
| `F2D_X`, `F2D_Y`, `F2D_ROTATION`, `F2D_SCALE_X`, `F2D_SCALE_Y`, `F2D_COLOR_R/G/B`, `F2D_ALPHA`, `F2D_TEXTURE` | id объекта | свойства объекта Fast2D |
| `F2D_IS_TOUCHED` | id | `1`, если объект нажат |
| `F2D_IS_TOUCHED_INDEX` | id, номер пальца | то же для конкретного пальца (по умолчанию 0) |
| `F2D_CAM_X`, `F2D_CAM_Y`, `F2D_CAM_ZOOM` | нет | камера Fast2D |
| `PT_ARGMAX` | имя тензора | индекс максимального элемента |
| `PT_VALUE` | имя, индекс | значение по плоскому индексу (не число: 0) |
| `PT_VALUEND` | имя, индексы строкой | значение по многомерному индексу |
| `PT_SHAPE` | имя | форма тензора |
| `PT_TOTALSIZE` | имя | общее число элементов |
| `PT_DUMP` | имя | содержимое тензора строкой |
| `PT_SAMPLE` | имя | случайный номер категории по распределению в тензоре |

**Текст с камеры, внешние устройства, пользовательские функции**

| Функция | Аргументы | Результат |
|---|---|---|
| `TEXT_BLOCK_FROM_CAMERA`, `TEXT_BLOCK_LANGUAGE_FROM_CAMERA` | номер блока | текст блока и его язык |
| `TEXT_BLOCK_X`, `TEXT_BLOCK_Y` | номер блока | координаты центра блока распознанного текста |
| `TEXT_BLOCK_SIZE` | номер блока | размер блока; все три функции при необходимости включают распознавание текста камерой |
| `ARDUINOANALOG` | пин 0–5 | значение аналогового пина; вне диапазона или нет устройства: `0` |
| `ARDUINODIGITAL` | пин 0–13 | значение цифрового пина; вне диапазона или нет устройства: `0` |
| `RASPIDIGITAL` | номер пина | `1` или `0` по состоянию пина Raspberry Pi; ошибка: `0` |
| значение, которого нет в `Functions` | аргументы по позициям | вызов пользовательской формулы из библиотеки `.newlib` (6.23); определение не найдено: `0`; определение есть, но библиотека не загружена: строка `LIB NOT FOUND`; функции нет в библиотеке: строка `FUNC NOT FOUND` |

**Что осталось без деталей:** тела функций `ID_OF_DETECTED_OBJECT` и `OBJECT_WITH_ID_VISIBLE`, а также форматы результатов `FLATTEN`, `TABLE_JOIN`, `COLLISION_LIST`, `INTERSECT_LIST`, `JSON_GET`/`JSON_SET` в сложных случаях.

### 6.28. Сериализатор XStream: алиасы, конвертеры, исключённые поля (`XstreamSerializer`, `batch2.txt`)

Источник: строки с `alias`, `registerConverter`, `omitField` из `XstreamSerializer.java` (раздел `XSTREAM_SERIALIZER` выгрузки `batch2.txt`). Именно здесь определяется, как класс называется в XML.

**Настройка**
- XStream создаётся с `PureJavaReflectionProvider` и сортировщиком ключей `CatroidFieldKeySorter`: он реализует порядок из `@XStreamFieldKeyOrder` (6.22); код сортировщика не присылался.
- Зарегистрированы конвертеры: `XStreamConcurrentFormulaHashMapConverter`, `XStreamUserDataHashMapConverter`, `XStreamUserVariableConverter`, `XStreamFormulaElementConverter`, `XStreamBrickConverter` (6.19), `XStreamScriptConverter`, `XStreamSpriteConverter`, `XStreamSettingConverter`. Конвертер `FormulaListConverter` закомментирован.

**Имена элементов (алиасы классов)**

| Имя элемента в XML | Классы |
|---|---|
| `look` | `LookData` |
| `sound` | `SoundInfo` |
| `nfcTag` | `NfcTagData` |
| `userVariable` | `UserVariable` |
| `userList` | `UserList` |
| `object` | `Sprite`, `GroupSprite`, `GroupItemSprite` (то есть `<object type="Sprite">`, `type="GroupSprite"` или `type="GroupItemSprite"`) |
| `script` | 24 классов: `Script`, `StartScript`, `WhenClonedScript`, `WhenScript`, `WhenConditionScript`, `WhenNfcScript`, `BroadcastScript`, `RaspiInterruptScript`, `WhenTouchDownScript`, `WhenBackgroundChangesScript`, `UserDefinedScript`, `EmptyScript`, `WhenGamepadButtonScript`, `WhenBounceOffScript`, `WhenSpriteReleasedScript`, `WhenFingerMovedOverSpriteScript`, `WhenFingerMovedOnScreenScript`, `BroadcastWithParamsReceiverScript`, `WhenNotificationClickedScript`, `WhenNotificationActionTriggeredScript`, `WhenAppMinimizedScript`, `WhenAppRestoredScript`, `WhenWindowResizedScript`, `WhenMqttMessageScript` |
| `brick` | 617 классов блоков (полный список по каталогу `content/bricks` приведён в 6.18 и 6.5; в алиасы входят и `PrepareSoundBrick2`, `StopSoundBrick2`, `ShowToastBlock`, `UnknownBrick`, а также класс с именем `ShowTextFontAction`) |
| `setting` | `LegoNXTSetting`, `LegoEV3Setting` |
| `nxtPort`, `ev3Port` | вложенные `LegoNXTSetting.NXTPort`, `LegoEV3Setting.EV3Port` |
| `Fast2DSetGravityBrick`, `WhenClonedWithNameBrick`, `WhenClonedWithNameScript` | каждый класс получил алиас, равный собственному имени, а не `brick` или `script` |

**Классы без алиаса `brick` или `script`.** По имени класса XStream, если алиаса нет, называет элемент полным именем класса (так в примерах `code.xml` из 6.6 выглядит `<org.catrobat.catroid.formulaeditor.FormulaElement>`: у `FormulaElement` алиаса нет). Из этого можно ожидать, что следующие классы пишутся не как `<brick type="…">`, а элементом с полным именем класса; для самих блоков это вывод по общему поведению XStream, а не проверенный пример:
- блоки: `ClearSceneBrick`, `CreateCubeBrick`, `CreateSpringConstraintBrick`, `PlayPreparedSoundBrick`, `PrepareSoundBrick`, `SavePlotBrick`, `SetObjectTextureBrick`, `SetSaveScenesBrick`, `SetStopSoundsBrick`, `ShowVarFontBrick`, `StartPlotBrick`, `StopPlotBrick`, `WhenAppMinimizedBrick`, `WhenAppRestoredBrick`, `WhenFingerMovedOnScreenBrick`, `WhenFingerMovedOverSpriteBrick`, `WhenNotificationActionTriggeredBrick`, `WhenSpriteReleasedBrick`, `WhenWindowResizedBrick`;
- скрипты: `AfterUpdateScript`, `BackPressedScript`, `BeforeUpdateScript`, `ExitProjectScript`, `WhenMouseButtonClickedScript`, `WhenMouseWheelScrolledScript`.
Служебные абстрактные классы (`Brick`, `FormulaBrick`, `CompositeBrick`, `EndBrick` и т. п., см. 6.18) алиаса не имеют, вероятно, потому что сами в XML не записываются.

**Поля, исключённые из XML** (`omitField`): у `Scene` это `originalWidth`, `originalHeight`; остальные:

| Класс | Поле |
|---|---|
| `Sprite` | `userBricks` |
| `LegacyDataContainer` | `userBrickVariableList` |
| `CameraBrick` | `spinnerValues` |
| `ChooseCameraBrick` | `spinnerValues` |
| `FlashBrick` | `spinnerValues` |
| `SetNfcTagBrick` | `nfcTagNdefDefaultType` |
| `SpeakAndWaitBrick` | `speechFile` |
| `SpeakAndWaitBrick` | `duration` |
| `StopScriptBrick` | `spinnerValue` |
| `ShowTextBrick` | `userVariableName` |
| `HideTextBrick` | `userVariableName` |
| `HideTextBrick` | `formulaList` |
| `HideTextBrick` | `userDataList` |
| `SayBubbleBrick` | `type` |
| `SayBubbleBrick` | `type` |
| `ThinkBubbleBrick` | `type` |
| `ThinkForBubbleBrick` | `type` |
| `StartScript` | `isUserScript` |
| `WhenScript` | `action` |
| `RaspiInterruptScript` | `receivedMessage` |
| `FadeParticleEffectBrick` | `formulaList` |
| `ParticleEffectAdditivityBrick` | `formulaList` |
| `SetParticleColorBrick` | `formulaList` |
| `NoneBrick` | `formulaList` |

Значит, перечисленные поля (например, `HideTextBrick.formulaList`, `WhenScript.action`, `StartScript.isUserScript`, `SpeakAndWaitBrick.speechFile`) в `code.xml` не появляются, даже если они есть в классе. Поля `Sprite.userBricks` и `LegacyDataContainer.userBrickVariableList` относятся к устаревшим структурам.

### 6.29. Хранение значений переменных и загрузка библиотек (`batch2.txt`)

**Значения переменных и списков.** В `code.xml` лежат только имя, `initialIndex` и ключ (`deviceValueKey` у переменной, `deviceListKey` у списка), сами значения не записываются (6.26). Функция `zipProjectWithoutSaves` исключает из архива файлы `DeviceVariables.json`, `DeviceLists.json` и `undo_code.xml`, а всё остальное (включая подкаталоги; каждый каталог записывается как запись `путь/`) упаковывает. Судя по именам, значения переменных и списков хранятся в `DeviceVariables.json` и `DeviceLists.json` в каталоге проекта (формат содержимого не показан). Экспорт через `ProjectExportTask` (6.25) упаковывает весь каталог проекта и, следовательно, включает эти файлы, если они есть. Где вызывается `zipProjectWithoutSaves`, по выгрузке не видно: функция лежит рядом с кодом отправки APK. Чтение и запись этих файлов выполняют классы `DeviceVariableAccessor` и `DeviceListAccessor` (пакет `io`). В `DeviceVariables.json` попадают переменные проекта, многопользовательские переменные проекта и переменные объектов; в `DeviceLists.json` списки проекта и списки объектов. Сам формат JSON реализован в базовом классе `DeviceUserDataAccessor`, который не присылался, поэтому формат неизвестен. При выгрузке проекта на сервер `ProjectUpload` отфильтровывает из списка файлов `DeviceVariables.json`; `DeviceLists.json` в этом фильтре не упомянут.

**Поля с инициализаторами-вызовами** (дополнение к 6.26)

| Класс | Поле Java | Тег или назначение |
|---|---|---|
| `Project` | `xmlHeader` | `header` |
| `Project` | `settings` (`List<Setting>`) | `settings` |
| `Project` | `userVariables` | `programVariableList` |
| `Project` | `multiplayerVariables` | `programMultiplayerVariableList` |
| `Project` | `userLists` | `programListOfLists` |
| `Project` | `sceneList` | `scenes` |
| `Project` | `broadcastMessageContainer` | не записывается (`transient`): сообщения собираются из блоков |
| `Scene` | `spriteList` | `objectList` |
| `Sprite` | `scriptList`, `lookList`, `soundList`, `nfcTagList`, `userVariables`, `userLists`, `userDefinedBrickList` (`List<Brick>`) | теги по имени поля |
| `Script` | `brickList` (`List<Brick>`), `scriptId` (`UUID`, при создании случайный) | теги по имени поля |
| `WhenConditionScript` | `formulaMap` (`ConcurrentFormulaHashMap`) | тег `formulaMap` (в выгрузке аннотаций алиаса нет; у блоков такая карта называется `formulaList`, 6.19) |

Соответствие тегов и полей `Project` и `Scene` подтверждено расположением аннотаций `@XStreamAlias` непосредственно над полями. У `Sprite` большая часть рабочих полей (`look`, `penConfiguration`, `plot`, `actionFactory` и др.) помечена `transient`.

**Когда загружаются библиотеки `.newlib`.** Вызов `LibraryManager.syncAndLoadLibraries` найден в двух местах (поиск шёл по всему `src/main/java`): `ProjectActivity` (строка 224, для только что загруженного проекта `loadedProject`) и `ProjectLibsFragment` (строка 186, после выбора файла). То есть библиотеки загружаются при открытии проекта в редакторе и при импорте библиотеки. Других вызовов нет, поэтому при запуске проекта без открытия редактора эти определения, судя по вызовам, не загружаются (если запуск не проходит через `ProjectActivity`; это вывод по отсутствию вызовов, а не проверенное поведение).

### 6.30. Порядок тегов и чтение элементов (`CatroidFieldKeySorter` и конвертеры XStream, `batch3.txt`)

**Порядок полей (`CatroidFieldKeySorter`)**
1. Если у класса или любого его предка есть `@XStreamFieldKeyOrder`, поля идут строго в порядке из списка (имя поля или его псевдоним). Если какого-либо **сериализуемого** поля (не `static`, не `transient`) в списке нет, сериализатор бросает `XStreamMissingSerializableFieldException`. Поэтому списки из 6.22 полные: у `Project` ровно 7 записываемых полей, у `Scene` 3, у `Sprite` 9, у `LanguageObject` 2.
2. Если аннотации нет (блоки, скрипты, `XmlHeader`, `LookData`, `SoundInfo` и др.), поля сортируются сначала по глубине класса в иерархии (поля базового класса раньше полей наследника), затем по алфавиту имени или псевдонима. Поля с `@XStreamAsAttribute` записываются атрибутами в открывающем теге.

Примеры порядка по этому правилу:
- блок: `brickId`, `commentedOut` (`BrickBaseType`), затем `formulaList` (`FormulaBrick`), затем поля самого блока по алфавиту (`presetSelection`, `userVariable` и т. д.); это совпадает с примерами `code.xml`;
- скрипт: атрибуты `posX`, `posY`; затем `brickList`, `commentedOut`, `scriptId` (поля `Script`), затем поля подкласса;
- `LookData`: атрибуты `lookId`, `name`, `fileName`, затем `isWebRequest`, `valid`;
- `XmlHeader`: все теги `<header>` по алфавиту имён и псевдонимов.

**Конвертеры (элементы и атрибуты)**

| Что | Как записывается и читается |
|---|---|
| Блоки, скрипты, объекты, настройки | атрибут `type` равен `getClass().getSimpleName()`. Скрипты, объекты (`Sprite`, `GroupSprite`, `GroupItemSprite`) и настройки (`LegoNXTSetting`, `LegoEV3Setting`) ищутся в пакете `org.catrobat.catroid.content`, блоки в двух пакетах (6.19). У объекта без `type` создаётся `Sprite`; значение `type="SingleSprite"` читается как `Sprite`. Неизвестный класс скрипта, объекта или настройки только пишется в лог |
| Формулы блока | каждая формула это `<formula category="ИМЯ_BrickField">…</formula>`, внутри лежат поля корневого `FormulaElement` (`type`, `value`, `leftChild`, …). Для пользовательских блоков вместо `category` пишется атрибут `input` с именем входа: `<formula input="имя">` |
| Чтение формул | значение `category` разбирается как `BrickField.valueOf(...)`: **неизвестное имя категории вызывает исключение**, то есть должно быть ровно одним из значений 6.1. Узел, который называется не `formula`, даёт формулу `0`. Если категория повторяется, остаётся первая (`putIfAbsent`) |
| Данные блока (`userDataList`) | `<userData category="…">` с вложенным `<userList>` или `<userVariable>`. Допустимые `category`: `ASSERT_LISTS_EXPECTED`, `ASSERT_LISTS_ACTUAL`, `FOR_ITEM_IN_USERLIST_LIST` (внутри список) и `FOR_ITEM_IN_USERLIST_VARIABLE` (внутри переменная), см. 6.2 |
| Переменная | `<userVariable type="UserVariable" serialization="custom">…` (как в примерах `code.xml`). Старый формат без `type`: текст элемента это просто имя переменной |
| `FormulaElement` | обычный разбор по полям; при чтении у узлов типа `SENSOR` старые имена заменяются новыми (таблица ниже) |

**Старые имена датчиков, заменяемые при чтении**

| Старое значение | Новое |
|---|---|
| `LEFT_PINKY_KNUCKLE_X/Y`, `RIGHT_PINKY_KNUCKLE_X/Y` | `LEFT_PINKY_X/Y`, `RIGHT_PINKY_X/Y` |
| `LEFT_INDEX_KNUCKLE_X/Y`, `RIGHT_INDEX_KNUCKLE_X/Y` | `LEFT_INDEX_X/Y`, `RIGHT_INDEX_X/Y` |
| `LEFT_THUMB_KNUCKLE_X/Y`, `RIGHT_THUMB_KNUCKLE_X/Y` | `LEFT_THUMB_X/Y`, `RIGHT_THUMB_X/Y` |
| `FACE_X_POSITION`, `FACE_Y_POSITION` | `FACE_X`, `FACE_Y` |
| `SECOND_FACE_X_POSITION` | `SECOND_FACE_X` |
| `SECOND_FACE_Y_POSITION` | `FACE_Y` (в коде именно так, вероятно, ошибка: ожидалось бы `SECOND_FACE_Y`) |

### 6.31. Группы объектов, настройки, версия языка (`batch3.txt`)

- **Группы объектов.** `GroupSprite` и `GroupItemSprite` не имеют собственных записываемых полей (`collapsed` помечено `transient`). Принадлежность к группе в XML не хранится, а определяется порядком в `objectList`: элементы `GroupItemSprite`, идущие подряд сразу после `GroupSprite`, считаются членами этой группы, пока не встретится объект другого типа.
- **Настройки.** `LegoNXTSetting` и `LegoEV3Setting` содержат массив `portSensorMapping` (по умолчанию `null`) из элементов `nxtPort` и `ev3Port`; у порта поля `number` (`int`) и `sensor` (перечисление датчика LEGO).
- **Версия языка.** `Constants.CURRENT_CATROBAT_LANGUAGE_VERSION = 1.18`. При сохранении проекта в `<header>` записывается эта версия. Проект с версией выше 1.18 или ниже 0.9 (кроме 0.8) не загружается; подробности и миграции в 6.33. Запросы к серверу передают параметр `max_version` с этим значением.
- **Файлы значений переменных.** Имена `DeviceVariables.json` и `DeviceLists.json` заданы константами `DEVICE_VARIABLE_JSON_FILE_NAME`, `DEVICE_LIST_JSON_FILE_NAME` и читаются из каталога проекта (`File(directory, …)`). `MainMenuActivity` при переборе записей каталога проекта пропускает эти два файла и `files` (контекст в выгрузке не показан).

### 6.32. Пользовательские блоки: определение, вызов и скрипт (`UserDefinedBrick`, `InputFormulaField`, `batch4.txt`)

Пользовательский блок («свой блок» в редакторе) состоит из трёх частей, связанных одним `userDefinedBrickID` (`UUID`):
1. **Определение**: `UserDefinedBrick` в списке `Sprite.userDefinedBrickList` (`<brick type="UserDefinedBrick">`, тег `isCallingBrick` равен `false`). Поле `userDefinedBrickDataList` хранит по порядку показа элементы двух видов: `UserDefinedBrickLabel` (текстовая метка, поле `label`) и `UserDefinedBrickInput` (вход, поле `input`).
2. **Тело**: скрипт `UserDefinedScript` с тем же `userDefinedBrickID` (поля скрипта в 6.26); его блок-шапка `UserDefinedReceiverBrick` хранит ссылки `userDefinedScript` и `userDefinedBrick` (6.21).
3. **Вызов**: `UserDefinedBrick` с `isCallingBrick` = `true` внутри списка блоков любого скрипта; у него те же `userDefinedBrickID` и список данных, а значения входов лежат в его `formulaList` в виде `<formula input="имя входа">…</formula>` (6.30).

**Ключ формулы.** `InputFormulaField` имеет единственное строковое поле `input`; равенство и хеш считаются по нему, `toString()` возвращает имя входа. Это и есть значение атрибута `input` у `<formula>`.

**Копирование.** `clone()` сохраняет `userDefinedBrickID` и признак вызова. При копировании вызывающего блока создаются новые входы (`new UserDefinedBrickInput(oldInput)`), а формулы перепривязываются к ключам новых входов (`copyFormulaOfInput`). Как формируется имя нового входа, в присланной части не видно; класс `UserDefinedBrickData` в выгрузку не входит.

### 6.33. Сохранение, загрузка и совместимость версий (`XstreamSerializer`, `ProjectManager`, `batch4.txt`)

**Сохранение и загрузка `code.xml`**
- При сохранении проект сначала пишется во временный файл `tmp_code.xml` и затем заменяет `code.xml` (в `XstreamSerializer` в одном месте создаются обе переменные: `tmp_code.xml` и `code.xml` каталога проекта).
- При загрузке, если `code.xml` нет, а `tmp_code.xml` есть, сериализатор пробует переименовать временный файл (по тексту сообщения об ошибке «code.xml did not exist. But wait, renaming …»); это защита от прерванного сохранения. Иначе бросается `LoadingProjectException`.
- `undo_code.xml` это копия `code.xml` для отмены правок: ею пользуются редактор скриптов (`ScriptFragment`) и редактор формул (`FormulaEditorFragment`). `ProjectExportTask` тоже обращается к этому файлу; что именно делает, по строке не видно.
- Каталог считается проектом, если в нём есть `code.xml` (список проектов, выбор файла; из списка исключаются каталоги `backpack` и `tmp`).
- Имя проекта это тег `<programName>` в `<header>`. При импорте, копировании и скачивании `XstreamSerializer.renameProject(code.xml, имя)` читает файл как текст UTF-8 и заменяет содержимое между `<programName>` и `</programName>` (новое имя кодируется для XML); если такого тега нет, возвращается `false`.
- При сохранении `Project.setDeviceData` заполняет заголовок: `platform` (константа `PLATFORM_NAME`), `platformVersion` (номер SDK Android), `deviceName` (модель устройства), версия языка, `applicationBuildName` и `applicationBuildNumber` (константы), `applicationVersion` и `applicationName` (из приложения; без контекста обе равны `unknown`).
- `permissions.txt` устарел: `ProjectManager.removePermissionsFile` удаляет его при загрузке проектов с версией языка не выше 0.99992. В проектах современного формата этого файла быть не должно.

**Каталоги сцен.** `Scene.getDirectory()` возвращает `<проект>/<имя сцены>`; спецсимволы имени кодируются (`encodeSpecialCharsForFileSystem`: имена `.` и `..` превращаются в `%2E`; иначе символы `%`, `"`, `/`, `:`, `<`, `>`, `?`, `\`, `|` заменяются на `%25`, `%22`, `%2F`, `%3A`, `%3C`, `%3E`, `%3F`, `%5C`, `%7C`; выгрузка показала только эти правила, возможны и другие), у сцены из рюкзака путь строится от каталога рюкзака. Есть и `Scene.getDirectoryNew()` с путём `<проект>` + `scenes/` + имя; где используется каждый метод, не показано. В XML у `LookData` и `SoundInfo` записано только имя файла (`fileName`), а путь вычисляет метод `getFile()` (его тело в выгрузку не попало), поэтому расположение `images/` и `sounds/` внутри каталога сцены подтверждено только описанием структуры от пользователя и константами из 6.25. `LookData.lookId` это случайный UUID в виде строки; объекты `LookData` считаются равными, если равны `lookId`; при чтении XML имя файла берётся из `fileName`, а сам файл (`file`) в XML не записывается.

**Проверка версии и миграции при загрузке (`ProjectManager.loadProject`, `batch5.txt`)**

| Версия языка проекта (`catrobatLanguageVersion`) | Что происходит |
|---|---|
| больше 1.18 | отказ: `OutdatedVersionProjectException` («устаревшая версия приложения») |
| меньше 0.9 и не равна 0.8 | отказ: `CompatibilityProjectException` |
| меньше 1.17 | включается флаг предупреждения о кэше физики |
| не больше 0.91 | `screenMode` принудительно `STRETCH` |
| не больше 0.992 | формулы столкновений приводятся к версии 0.993 (`updateCollisionFormulasTo993`) |
| не больше 0.993 | формулы цвета пера (`updateSetPenColorFormulasTo994`) |
| не больше 0.994 | значения Arduino (`updateArduinoValuesTo995`) |
| не больше 0.995 | скрипты столкновений (`updateCollisionScriptsTo996`) |
| не больше 0.999 | «поверхностные» копии заменяются полными (`makeShallowCopiesDeepAgain`) |
| не больше 0.9993 | **плоские списки блоков преобразуются в дерево** (`updateScriptsToTreeStructure`, `BrickTreeBuilder`): вложенные блоки попадают в поля-списки составных блоков, см. 6.21 |
| не больше 0.99992 | удаляется устаревший файл `permissions.txt` (`removePermissionsFile`) |
| не больше 0.9999995 | `updateBackgroundIndexTo9999995` (по названию, индекс фона) |
| меньше 999.9 при отключённой сборочной опции `FEATURE_LIST_AS_BASIC_DATATYPE` | `flattenAllLists` (по названию, «разворачивание» вложенных списков) |
| не больше 1.03 | свойство направления в формулах (`updateDirectionProperty`) |
| не больше 1.13 | `customResolution` = `false` |
| не больше 1.14 | `physicsWidthArea` = `3.0`, `physicsHeightArea` = `2.0` |
| не больше 1.15 | `gitRemoteUrl` = `""` |
| меньше 1.17 | `migrateProjectToV1_17` (новые UUID), при изменениях проект сразу сохраняется заново |
| меньше 1.18 | `migrateProjectToV1_18`, при изменениях проект сразу сохраняется заново |

После миграций в проект записывается версия 1.18, затем выполняются `localizeBackgroundSprites` (по названию и по передаваемой строке `background`, подстановка локализованного имени фона), `initializeScripts`, загрузка настроек LEGO и вычисление требуемых ресурсов проекта. По найденным ресурсам приложение **автоматически включает соответствующие настройки**: Phiro, Arduino, распознавание речи, распознавание лиц, поз, текста и объектов, синтез речи (для списка `Resources` из 6.3). Принимаются версии 0.8 и от 0.9 до 1.18.

**Загрузка библиотек.** `ProjectActivity` вызывает `LibraryManager.syncAndLoadLibraries` сразу после загрузки проекта (в журнал пишется «Проект … загружен, запускаю синхронизацию библиотек»), затем при необходимости показывает предупреждение о кэше физики (6.29).

## 7. Сверка с реальными проектами

Ниже: результаты сравнения описания из разделов 1–6 с настоящими файлами `.newtrobat` (все записаны NewCatroid 2.2.0, язык 1.18; один импортирован из Pocket Code). Что подтвердилось и что оказалось иначе, указано для каждого проекта.

| Раздел | Файл | Что проверено |
|---|---|---|
| 7.1 | `квадраты тест (FPS) 2.0` | 4 сцены, Fast2D, пользовательский блок, переменные, `DeviceVariables.json`, имена файлов образов |
| 7.2 | `For_Claude_67`, `For_Claude_6752` | библиотека `.newlib`, пользовательская формула и блок, 3D, группа объектов, `DeviceLists.json`, `.rscene` |
| 7.3 | `For_Claude_52` | звук, настройки LEGO NXT, NFC, имена образов, многопользовательские переменные |
| 7.4 | `For_Claude_42` | `CustomBrick` с параметром (`CUSTOM_PARAM_n`), Raspberry Pi, LEGO EV3, звуки `.mid` и `.mp3` |
| 7.5 | `Хитрость` | проект из Pocket Code, блоки Arduino, `LoadSceneBrick` с `.rscene`, `CustomBrick` с двумя параметрами |
| 7.6 | `PockeTensor+Fast2D (1)` | блоки PockeTensor, формат `files/model.bin`, ссылка на отсутствующую библиотеку |

### 7.1. Сверка с реальным проектом (`квадраты тест (FPS) 2.0`, версия NewCatroid 2.2.0, язык 1.18)

Проанализирован настоящий файл `.newtrobat` (4 сцены, 14 объектов, 32 типа блоков, пользовательский блок, переменные на устройстве, сцена на Fast2D). Ниже: как выглядит архив, что подтвердилось и что оказалось иначе.

**Содержимое архива (32 записи, все файлы; записей-каталогов нет, `code.xml` идёт первым)**
```
code.xml
manual_screenshot.png
DeviceVariables.json
files/                      <- произвольные файлы проекта (png, otf, …), плоско
<Имя сцены>/                <- по одному каталогу на сцену; имя совпадает с <name> сцены (допустимы пробел и кириллица: "Fast 2D", "Меню")
    automatic_screenshot.png
    images/   (.nomedia + изображения)
    sounds/   (.nomedia + звуки)
```
В этом проекте нет `libs/`, `permissions.txt`, `tmp_code.xml`, `undo_code.xml`, `DeviceLists.json`: они не обязательны. Файлы `.nomedia` лежат внутри `images/` и `sounds/` каждой сцены (то есть не в корне проекта). Имена файлов изображений остаются «человеческими» (без хеша); при совпадении имён к имени добавляется суффикс `_#0`, `_#1`, `_#2` перед расширением (`Мой актер или объект_#0.png`); у импортированных изображений бывают числовые имена (`1001085547.png`). Атрибут `look/@fileName` совпадает с именем файла в `<сцена>/images/` у всех образов, лишних файлов нет; `look/@name` от имени файла не зависит. Файлы из `files/` в формулах указаны простыми относительными именами в строках (`Blogger Sans-Bold.otf`).

**`DeviceVariables.json`** (47 байт): плоский объект `{"<deviceValueKey>": число}`. Пример: `{"59ac87de-…": 1430.0}`. Ключ равен `deviceValueKey` переменной «Лучший Fast», у которой в проекте есть блок записи на устройство; у остальных переменных записей нет. То есть в файле хранятся только значения переменных, записанных на устройство блоком записи (`WriteVariableOnDeviceBrick`), а не всех переменных.

**Что подтвердилось**
- Порядок и имена верхнего уровня `<program>` (6.22, 6.30): `header`, `settings`, `scenes`, `programVariableList`, `programListOfLists`, `programMultiplayerVariableList`, `disableScientificNotation`.
- `<scene sceneId="…">` с `name`, `objectList`; `<object type="Sprite" spriteId="…" name="…">` с детьми в порядке `lookList`, `soundList`, `scriptList`, `nfcTagList`, `userVariables`, `userLists`, `userDefinedBrickList`; `<script type="…" posX posY>` с детьми `brickList`, `commentedOut`, `scriptId` и затем полями подкласса по алфавиту (`screenRefresh`, `userDefinedBrickID`, `userDefinedBrickInputs`; у `WhenConditionScript` это `formulaMap`).
- Заголовок `<header>`: теги идут по алфавиту (`screenHeight`, `screenMode`, `screenWidth` между `scenesEnabled` и `tags`), все поля из таблицы 6.26 присутствуют.
- Составные блоки (6.21): `loopBricks` у `RepeatBrick` и `ForeverBrick`, `ifBranchBricks` у `IfThenLogicBeginBrick`. Простые поля блоков: `sceneToStart` (имя сцены), `spinnerSelection` у `StopScriptBrick`, `type` (`DYNAMIC`, `FIXED`) у `SetPhysicsObjectTypeBrick`, `alignmentSelection` у `ShowTextFontBrick` и `ShowVarFontBrick`.
- Порядок тегов блока: `brickId`, `commentedOut`, `formulaList`, поля базового класса (`userVariable`), затем поля самого блока (`alignmentSelection` стоит после `userVariable`): это правило глубины из 6.30.
- Таблицы 6.20 и 6.21: у 92 из 93 блоков с формулами все `category` входят в допустимый набор из 6.20; единственное расхождение это `UserDefinedBrick`, у которого ключ формулы не `BrickField`, а имя входа. Собственные поля данных всех 32 типов блоков совпали с 6.21, кроме `CloneBrick` (см. ниже).
- `<org.catrobat.catroid.content.bricks.ShowVarFontBrick type="ShowVarFontBrick">`: блок без алиаса записывается элементом с полным именем класса и атрибутом `type` (6.28, предсказание подтвердилось). Все остальные блоки идут как `<brick type="…">`.
- Формулы: `<formula category="…">` с детьми `additionalChildren`, `leftChild`, `rightChild`, `type`, `value` в таком порядке; встречены типы узлов `NUMBER`, `STRING`, `OPERATOR`, `FUNCTION`, `SENSOR`, `USER_VARIABLE`, `USER_DEFINED_BRICK_INPUT`; значения (`RAND`, `JOIN`, `FPS`, `MINUS`, `PLUS`, `GREATER_THAN`, `SMALLER_OR_EQUAL`) есть в перечислениях 6.7–6.9. Для ключа пользовательского блока записан `<formula input="Имя ввода">`.
- Переменная в блоке: `<userVariable type="UserVariable" serialization="custom"><userVariable><default><initialIndex/><deviceValueKey/><name/></default></userVariable></userVariable>`; список в блоке: `<userList><deviceListKey/><initialIndex/><name/></userList>` (без `type`).
- Ссылки (`reference`): `programVariableList`, `programListOfLists` и `look` в `SetLookBrick` содержат только `<… reference="относительный путь"/>` (пути вида `../../scenes/scene[2]/objectList/object[2]/…/brick[3]/userVariable`, в том числе через элемент `org.catrobat.catroid.content.bricks.ShowVarFontBrick`; индекс `[n]` считается среди одноимённых соседей).
- Скрипты: `StartScript`, `WhenScript`, `WhenClonedScript`, `WhenConditionScript`, `UserDefinedScript`. Поле `formulaMap` у `WhenConditionScript` содержит `<formula category="IF_CONDITION">`.

**Что оказалось иначе или уточнилось**
- Тег поля `UserDefinedBrick.isCallingBrick` в файле называется `isCallingBrick`, а не `callingBrick`: аннотация `@XStreamAlias("callingBrick")` на запись не повлияла (исправлено в 6.21, 6.22, 6.32).
- `automatic_screenshot.png` лежит в каталоге **каждой сцены**; в корне проекта лежит `manual_screenshot.png`, а во втором и третьем проектах (7.2) в корне лежит ещё и `automatic_screenshot.png`. То есть корневой снимок бывает ручным или автоматическим, а снимок в каталоге сцены автоматический (в 6.25 это было описано неточно).
- Поле со значением `null` в XML не пишется: у `CloneBrick` без выбранного объекта нет тега `objectToClone`. Пустая карта формул пишется как `<formulaList/>` (так у `ReadListFromDeviceBrick`, `WriteListOnDeviceBrick` и у определения `UserDefinedBrick`), а у блоков, не наследующих `FormulaBrick` (`ForeverBrick`, `SceneStartBrick`, `SetLookBrick`, `SetPhysicsObjectTypeBrick`, `StopScriptBrick`, `CloneBrick`, `ReadVariableFromDeviceBrick`, `WriteVariableOnDeviceBrick`), тега `formulaList` нет вовсе.
- Определение пользовательского блока и его вызов делят один объект: у определения (`isCallingBrick=false`) в `userDefinedBrickList` поле `userDefinedBrickDataList` записано как `<userDefinedBrickDataList reference="../../../scriptList/script/brickList/brick[3]/userDefinedBrickDataList"/>`, то есть ссылкой на список вызывающего блока. Сам список содержит `<userDefinedBrickLabel><type>LABEL</type><label>текст</label></userDefinedBrickLabel>` и `<userDefinedBrickInput><type>INPUT</type><initialIndex>0</initialIndex><input><input>Имя ввода</input></input></userDefinedBrickInput>`.
- `UserDefinedScript.userDefinedBrickInputs` содержит элементы `<userVariable type="UserVariable" serialization="custom">` с именем входа (например, «Имя ввода»), `initialIndex` равен `-1`; в формулах тела блока на них указывает узел `USER_DEFINED_BRICK_INPUT`.
- У блока `ReadVariableFromDeviceBrick` в файле значение `initialIndex` у переменной бывает не только `0` или `-1` (встречено `3`); как оно вычисляется, по проекту не видно.
- В этом проекте `<settings/>` пусто, а `physicsWidthArea` и `physicsHeightArea` равны `1.0` (не значения по умолчанию из 6.26).

### 7.2. Сверка с проектом `For_Claude_67` и `For_Claude_6752` (библиотека, 3D, группа объектов)

Два архива содержат один и тот же `code.xml` (22 100 байт, побайтово одинаков); во втором добавлен `DeviceLists.json`, а снимок сцены обновлён. Версия NewCatroid 2.2.0, язык 1.18, одна сцена «Сцена», три объекта.

**Содержимое архива**
```
code.xml
automatic_screenshot.png            <- в корне
DeviceLists.json                    <- только во втором архиве
libs/bilibiliteka.newlib            <- библиотека (ZIP)
files/Shahed-136.obj                <- модель (Wavefront OBJ, ~1 МБ)
files/scene.rscene, scenee.rscene   <- 3D-сцены (JSON, см. ниже)
Сцена/automatic_screenshot.png
Сцена/images/ (.nomedia, 1001122278.png, 1001122284.png)
Сцена/sounds/ (.nomedia)
```
Это подтверждает, что каталог `libs/` и файлы `files/` попадают в `.newtrobat` при экспорте (6.25). `code.xml` не ссылается ни на `libs/bilibiliteka.newlib` по имени, ни на файлы из `files/`: библиотека находится сканированием каталога `libs/`, а `.obj` и `.rscene` могут использоваться блоками по имени из других проектов.

**`DeviceLists.json`**: плоский объект `{"<deviceListKey>": [значения]}`; пример `{"125edefb-d49d-4986-bec4-85555ac0e28e": [220.0, "окак"]}`. Числа записываются как числа с плавающей точкой, строки как строки, типы смешиваются в одном списке. Ключ равен `deviceListKey` списка в `code.xml`; запись создаёт блок `WriteListOnDeviceBrick` (формат `DeviceVariables.json` аналогичен, 7.1).

**Библиотека `bilibiliteka.newlib`** (ZIP из трёх файлов: `code.txt`, `formulas.xml`, `bricks.xml`, 6.23):
- `code.txt` на LunoScript: функции `sum(a, b)` (возвращает `Number(a) + Number(b)`) и `toast(sprite, text)` (вызывает `MakeToast("Text is: " + String(text))`). Судя по сигнатуре `toast(sprite, text)`, первым аргументом функции блока передаётся объект (`sprite`), остальными значения параметров; в присланных строках загрузчика это не показано.
- `formulas.xml`: формула `id="29481"`, `function="sum"`, `displayName="Сумма"` с двумя параметрами `NUMBER` по умолчанию `4` и `7`.
- `bricks.xml`: блок `id="5391938"`, `function="toast"`, `header="Тост {0} {о}"` без параметров (метки в заголовке не обязаны соответствовать числу параметров: здесь `{0}` и опечатка `{о}`, а параметров ноль).

**Связь `code.xml` и библиотеки (подтверждено)**
- Формула: в `SetVariableBrick` узел `FUNCTION` со значением `29481` (это `id` из `formulas.xml`), `leftChild` = `4`, `rightChild` = `7`: аргументы идут в обычном порядке (6.27).
- Блок: `<brick type="CustomBrick">` с `<formulaList/>` (пустой), `<definitionId>5391938</definitionId>` (это `id` из `bricks.xml`) и `<parameterFormulas/>` (пусто, так как параметров нет; пример с параметром в 7.4). Теги идут в порядке `brickId`, `commentedOut`, `formulaList`, `definitionId`, `parameterFormulas`.

**Что видно в блоках**
- `TryCatchFinallyBrick`: теги списков записаны **по алфавиту**, а не по порядку выполнения: `catchBricks`, `finallyBricks`, `tryBricks`. Блок может быть закомментирован (`commentedOut` = `true`, как в этом файле).
- `IfLogicBeginBrick`: `formulaList` (`IF_CONDITION`), затем `elseBranchBricks`, затем `ifBranchBricks`; вложенность произвольной глубины (в файле «если» внутри «иначе»). Тега `elseIfBranches` в файле нет (поле, вероятно, `null` без веток «иначе если» и поэтому не записывается).
- Вызовы одного пользовательского блока (`isCallingBrick` = `true`) делят список `userDefinedBrickDataList`: полностью он записан у первого по порядку документа, у остальных вместо него `<userDefinedBrickDataList reference="../../../elseBranchBricks/brick/…"/>`. Определение (`isCallingBrick` = `false`) в `userDefinedBrickList` тоже ссылается на этот список. Имена входов здесь `0` и `500` (`<input><input>0</input></input>`), а значения в формулах вызова `0` и `400`; в предыдущем проекте имя входа было «Имя ввода», то есть имя входа произвольно. Формула `<formula input="0">` лежит в `formulaList` вызова.
- Порядок элементов `<formula>` внутри `formulaList` **не алфавитный и не по номерам**: `Set3dPositionBrick` записан как `VALUE_1`, `VALUE_2`, `VALUE_4`, `VALUE_3`, `ShowVarFontBrick` как `COLOR`, `FILE`, `SIZE`, `Y_POSITION`, `X_POSITION`. Это порядок обхода хеш-карты, поэтому парсер не должен полагаться на порядок формул.
- Поля 3D и физики: `ThreedCreateCylinderBrick` (формула `VALUE_1`), `Set3dPositionBrick` (`VALUE_1`…`VALUE_4`), `SetPhysicsStateBrick` (формулы `VALUE_1`, `VALUE_2` и целые `shapeSelection`, `stateSelection`), `SetPhysicsObjectTypeBrick` (`type` = `DYNAMIC`), `ApplyForceBrick` (`FORCE_X`, `FORCE_Y`). Что означают номера `VALUE_n` у 3D-блоков, по `code.xml` не видно; в таблице 6.20 они указаны только по именам.
- `AddItemToUserListBrick` и `WriteListOnDeviceBrick` указывают на один список через `reference` (`../../brick[3]/userList`).

**Группа объектов (подтверждено).** В `objectList` идут по порядку объекты `GroupSprite` («чвцжв») и `GroupItemSprite` («смки»); у обоих те же теги, что у `Sprite` (пустые `lookList`, `soundList`, `scriptList` и т. д. у группы). Принадлежность к группе определяется порядком (6.31). Имя образа у импортированных картинок совпадает с именем файла без расширения (`name="1001122284"`, `fileName="1001122284.png"`).

**Файл `.rscene`** (в `files/`, JSON, 3D-сцена движка Raptor; оба файла в проекте побайтово совпадают):
- верхний уровень: `ambientIntensity`, `csmSplitFactor`, `gameObjects` (массив), `renderSettings` (`numBones`, `numDirectionalLights`, `numPointLights`, `numSpotLights`), `shadowResolution`, `shadowSize`, `skyR`, `skyG`, `skyB`, `skyboxPath`, `useCSM`;
- элемент `gameObjects`: `id`, `name`, `isActive`, `parentId`, `childrenIds`, `transform` (`position` x, y, z; `rotation` w, x, y, z; `scale` x, y, z) и массив `components`, где у каждого компонента поле `class` задаёт тип: `org.catrobat.catroid.raptor.RenderComponent` (поле `modelFileName`, например `"primitive:cube"`) и `org.catrobat.catroid.raptor.MaterialComponent` (цвета `baseColor` и `emissiveColor` с `r`, `g`, `b`, `a`, пути текстур, `metallic`, `roughness`, `emissiveIntensity`, `uvScaleX`, `uvScaleY`).
Полный набор типов компонентов по одному примеру неизвестен; код чтения и записи `.rscene` не присылался.

### 7.3. Сверка с проектом `For_Claude_52` (звук, LEGO NXT, NFC, настройки, образы)

Проект записан NewCatroid 2.2.0 (`applicationBuildType` = `signedRelease`, язык 1.18, `platformVersion` 36). В архиве: `code.xml`, `automatic_screenshot.png` (в корне), `Сцена/automatic_screenshot.png`, `Сцена/images/` (4 png и `.nomedia`), `Сцена/sounds/` (`click.wav`, `.nomedia`). Блоков «если / иначе если / иначе» в проекте нет (это замечание о версии 2.3.0, см. 6.21), поэтому формат `elseIfBranches` по-прежнему не проверен на реальном файле.

**Звук**
- Элемент: `<sound fileName="click.wav" name="click" soundId="UUID"><midiFile>false</midiFile></sound>`: три атрибута и тег `midiFile` (`boolean`). Файл лежит в `<сцена>/sounds/` под тем же именем.
- `PlaySoundBrick` хранит звук ссылкой: `<sound reference="../../../../../soundList/sound"/>`, `StartRecordingBrick` не имеет полей, `StopRecordingBrick` имеет формулу `FILE_NAME`.

**Настройки LEGO NXT** (подтверждено, 6.31):
```xml
<settings>
  <setting type="LegoNXTSetting">
    <portSensorMapping>
      <nxtPort><number>0</number><sensor>NO_SENSOR</sensor></nxtPort>
      <nxtPort><number>1</number><sensor>LIGHT_INACTIVE</sensor></nxtPort>
      <nxtPort><number>2</number><sensor>TOUCH</sensor></nxtPort>
      <nxtPort><number>3</number><sensor>NO_SENSOR</sensor></nxtPort>
    </portSensorMapping>
  </setting>
</settings>
```
Значения `sensor`: `NO_SENSOR`, `LIGHT_INACTIVE`, `TOUCH` (перечисление датчика LEGO, полный список не показан).

**Блоки LEGO и NFC**
- `LegoNxtMotorMoveBrick` (формула `LEGO_NXT_SPEED`, тег `motor` = `MOTOR_A`), `LegoNxtMotorTurnAngleBrick` (`LEGO_NXT_DEGREES`, `motor`), `LegoNxtMotorStopBrick` (только `motor`), `LegoNxtPlayToneBrick` (`LEGO_NXT_DURATION_IN_SECONDS`, `LEGO_NXT_FREQUENCY`). Тег `motor` хранит имя значения перечисления строкой. В формулах датчики LEGO записываются как `SENSOR` со значениями `NXT_SENSOR_2`, `NXT_SENSOR_3` (6.7).
- `SetNfcTagBrick`: формула `NFC_NDEF_MESSAGE` и целое поле `nfcTagNdefType` (в файле `2`); `nfcTagList` объектов при этом пуст.

**Образы и имена**
- Имя образа внутри объекта делается уникальным добавлением суффикса: `gh` и `gh (1)`, `yy` и `yy (1)`.
- Имя файла `Мой актер или объект.png` у второго объекта получает `_#0` (`Мой актер или объект_#0.png`): суффикс `_#N` уникализирует **имя файла** внутри каталога сцены.
- `GroupSprite` «by» без членов: следующие за ним объекты `gh` и `yy` имеют тип `Sprite`, а не `GroupItemSprite`, то есть в группу не входят (правило порядка из 6.31).

**Многопользовательские переменные.** `programMultiplayerVariableList` может содержать ссылку на переменную из блока: `<userVariable reference="../../scenes/scene/objectList/object/scriptList/script/brickList/brick/userVariable"/>`, при этом `programVariableList` пуст. Переменная, связанная с многопользовательским режимом, записывается в списке проекта ссылкой на своё первое определение в блоке.

### 7.4. Сверка с проектом `For_Claude_42` (CustomBrick с параметром, Raspberry Pi, LEGO EV3, NFC, звуки)

Проект записан NewCatroid 2.2.0, язык 1.18. В архиве: `code.xml`, `automatic_screenshot.png` (корень и каталог сцены), `libs/kaksа.newlib` (в имени файла кириллическая «а»: имена `.newlib` могут быть не только ASCII), `files/gt.rscene`, `Сцена/sounds/` (`Фигня 1.mid`, `popular-riser-metallic-sound-effect (2).mp3`). Блоков Arduino в проекте нет (по сообщению пользователя, их сейчас невозможно поставить из-за ошибки в приложении), поэтому они на реальном файле не проверены.

**Пользовательский блок с параметром (`CustomBrick`)**
```xml
<brick type="CustomBrick">
  <brickId>…</brickId>
  <commentedOut>false</commentedOut>
  <formulaList>
    <formula category="CUSTOM_PARAM_1"> …формула…</formula>
  </formulaList>
  <definitionId>5391938</definitionId>
  <parameterFormulas>
    <org.catrobat.catroid.formulaeditor.Formula>
      <formulaTree reference="../../../formulaList/formula"/>
      <sceneFirstStart>false</sceneFirstStart>
    </org.catrobat.catroid.formulaeditor.Formula>
  </parameterFormulas>
</brick>
```
- Значения параметров лежат в `formulaList` под категориями `CUSTOM_PARAM_1`, `CUSTOM_PARAM_2`, … (значения `BrickField` из 6.1, до `CUSTOM_PARAM_10`); номер, по-видимому, соответствует индексу параметра (метке `{0}` отвечает `CUSTOM_PARAM_1`); это вывод по одному примеру.
- `parameterFormulas` это список объектов `Formula` (класс без алиаса, поэтому элемент называется полным именем `org.catrobat.catroid.formulaeditor.Formula`). У каждого есть поля `formulaTree` (корневой узел формулы) и `sceneFirstStart` (`boolean`). В этом файле `formulaTree` записан ссылкой на ту же формулу в `formulaList`: два списка указывают на одни и те же объекты. Для `.newlib` из этого проекта параметр объявлен как `<param type="TEXT_FIELD" name="{0}" />`, заголовок `Тост {0}`; а в формуле параметра вызывается пользовательская функция `29481(42, 67)`.

**Raspberry Pi**
- `RaspiIfLogicBeginBrick`: `formulaList` (`IF_CONDITION`), затем `elseBranchBricks`, `ifBranchBricks` (поля наследуются от `IfLogicBeginBrick`).
- `RaspiPwmBrick`: формулы `RASPI_PWM_PERCENTAGE`, `RASPI_PWM_FREQUENCY`, `RASPI_DIGITAL_PIN_NUMBER`.
- `RaspiSendDigitalValueBrick`: формулы `RASPI_DIGITAL_PIN_NUMBER`, `RASPI_DIGITAL_PIN_VALUE`.

**LEGO EV3**
- `LegoEv3SetLedBrick`: нет `formulaList`, одно поле `ledStatus` со строкой имени значения (`LED_ORANGE_FLASHING`).
- `LegoEv3MotorMoveBrick`: формула `LEGO_EV3_SPEED`, поле `motor` (`MOTOR_B_C`). `LegoEv3MotorTurnAngleBrick`: `LEGO_EV3_DEGREES`, `motor` (`MOTOR_C`). `LegoEv3PlayToneBrick`: `LEGO_EV3_FREQUENCY`, `LEGO_EV3_DURATION_IN_SECONDS`, `LEGO_EV3_VOLUME`.
- Тег `motor` стоит после `formulaList` (поле подкласса идёт после поля `FormulaBrick`, 6.30).

**NFC и сцены**
- `SetNfcTagBrick`: `nfcTagNdefType` принимает значения от `0` до `7` (все восемь встречены в файле); формула `NFC_NDEF_MESSAGE`.
- `WhenNfcScript`: после `brickList`, `commentedOut`, `scriptId` идёт `matchAll` (`true`); поле `nfcTag` отсутствует, так как равно `null` и не записывается.
- `LoadSceneBrick` использует формулу с категорией `VALUE` (имя сцены задаётся формулой), в отличие от `SceneStartBrick` с полем `sceneToStart` (6.21).

**Звуки**
- В `soundList` лежат два элемента `<sound fileName name soundId><midiFile>false</midiFile></sound>`; тег `midiFile` равен `false` даже для файла `.mid`, то есть он не вычисляется по расширению (смысл поля по `code.xml` неизвестен).
- Имена файлов звуков могут содержать пробелы и скобки (`popular-riser-metallic-sound-effect (2).mp3`); `sound/@name` равно имени файла без расширения. Два блока `PlaySoundBrick` ссылаются на разные звуки: `soundList/sound` и `soundList/sound[2]`.

**`.rscene` (второй пример).** В `gt.rscene` два объекта: `Empty` (без компонентов, позиция 0, 0, 0) и `Cube` (`RenderComponent` и `MaterialComponent`, позиция x ≈ 13.1); верхний уровень и вложенные поля те же, что в 7.2.

### 7.5. Сверка с проектом `Хитрость` (импорт из Pocket Code, Arduino, `LoadSceneBrick`)

Проект создан в Pocket Code, импортирован в NewCatroid, дополнен блоками NewCatroid и экспортирован как `.newtrobat`. В архиве: `code.xml`, `automatic_screenshot.png` (корень и каталог сцены), `libs/Новая библиотека (7).newlib` (имя файла с пробелами и скобками), `files/hf.rscene`, пустые `Сцена/images/` и `Сцена/sounds/` (только `.nomedia`).

**Заголовок и совместимость с Pocket Code**
- В `<header>` остались значения исходной программы: `applicationName` = `Покет Код` (локализованное название), `applicationVersion` = `1.4.3`, `catrobatLanguageVersion` = `1.18`, `platform` = `Android`. При этом в `scriptList` лежат блоки, которых нет в Pocket Code (`CustomBrick`, `CreateCubeBrick`). Судя по этому, заголовок не обновляется при каждом сохранении (или не обновляется при экспорте), и `applicationName`, `applicationVersion` не обязательно описывают программу, записавшую файл последней.
- Pocket Code 1.4.3 пишет тот же язык 1.18 и ту же структуру `code.xml`, поэтому по таблице 6.33 для такого проекта версионные миграции не нужны.

**Блоки Arduino (подтверждено)**
- `ArduinoSendDigitalValueBrick`: формулы `ARDUINO_DIGITAL_PIN_VALUE` и `ARDUINO_DIGITAL_PIN_NUMBER`.
- `ArduinoSendPWMValueBrick`: формулы `ARDUINO_ANALOG_PIN_VALUE` и `ARDUINO_ANALOG_PIN_NUMBER`.
- Оба блока здесь закомментированы (`commentedOut` = `true`). В формулах пинов встречены `FUNCTION` `ARDUINOANALOG` и `ARDUINODIGITAL` с одним числовым аргументом в `leftChild` (6.27); категория пина и функция в этом файле не совпадают по названию, то есть это содержимое формул пользователя, а не правило.
- Категории формул совпали с таблицей 6.20.

**`LoadSceneBrick` и `.rscene`**
- `LoadSceneBrick` с формулой `VALUE` = строка `hf.rscene` соответствует файлу `files/hf.rscene`: значением задаётся имя файла 3D-сцены из каталога `files/`. Это связывает `.rscene` с `code.xml` (7.2).
- `CreateCubeBrick` записан элементом `<org.catrobat.catroid.content.bricks.CreateCubeBrick type="CreateCubeBrick">` (6.28: блок без алиаса); формула `VALUE` задаёт имя создаваемого объекта (`myObject`).
- В `hf.rscene` три объекта (`Sphere`, `Cube (1)`, `Cube`): повторяющееся имя получает суффикс ` (1)`.

**`CustomBrick` с двумя параметрами**
- В `formulaList` лежат `CUSTOM_PARAM_1` и `CUSTOM_PARAM_2`, а `parameterFormulas` содержит два объекта `Formula`, чьи `formulaTree` ссылаются на `../../../formulaList/formula` и `../../../formulaList/formula[2]`: индекс `[2]` показывает порядок формул в `formulaList`. Порядок `parameterFormulas` совпадает с номерами параметров, что подтверждает вывод 7.4.
- В `bricks.xml` проекта: `header="Сумма {0} и {1}"`, два `<param>` с именами `{0}` и `{1}`; у первого `type="ПОКАЧТОТУТВСЕГДАTEXT_FIELD"` (произвольная строка). Блок всё равно читается как `TEXT_FIELD`, то есть неизвестное значение `type` не вызывает ошибки (6.23). `formulas.xml` может быть пустым: `<formulas />`.
- `id` блока здесь тот же `5391938`, что в другой библиотеке (7.2): идентификаторы блоков разных библиотек могут совпадать (при загрузке второй перезапишет первый с предупреждением, 6.23).

### 7.6. Сверка с проектом `PockeTensor+Fast2D (1)` (PockeTensor, `model.bin`, ссылка на отсутствующую библиотеку)

Проект записан NewCatroid 2.2.0, язык 1.18, один объект с одним `StartScript`. Блоков Fast2D в нём нет, поэтому Fast2D этим файлом не проверен. В архиве: `code.xml`, `Сцена/automatic_screenshot.png` (корневого снимка нет), `Сцена/sounds/Фигня 1.mid` (звук не используется в блоках), `files/model.bin`, каталога `libs/` нет.

**Блоки PockeTensor (подтверждено, категории совпали с таблицей 6.20)**
- `PtCreateTensorBrick`: формулы `VALUE_1` (форма тензора строкой: `"10,4"`), `VALUE_2` (`0.0`), `VALUE_3` (`1`), `NAME` (имя тензора: `"tensor"`). В XML они записаны в порядке `VALUE_1`, `VALUE_2`, `VALUE_3`, `NAME` (порядок обхода хеш-карты, 7.2). Смысл `VALUE_2` и `VALUE_3` по `code.xml` не определить; данные тензора в `model.bin` заполнены нулями, что согласуется с `VALUE_2` = `0.0` как значением заполнения (вывод по одному примеру).
- `PtSetTrainingBrick`: формула `VALUE_1` (`1`, по названию режим обучения включён).
- `MLSaveBrick`: формула `STRING` = `"model.bin"`; имя файла относится к каталогу `files/` проекта, и файл `files/model.bin` в архиве действительно есть.

**Формат `files/model.bin`** (186 байт; разобран полностью, все байты учтены; числа little-endian)

| Размер | Поле | В этом файле |
|---|---|---|
| 4 байта | `int32` число тензоров | `1` |
| для каждого тензора: 4 байта | `int32` длина имени | `6` |
| длина имени байт | имя тензора (UTF-8) | `tensor` |
| 4 байта | `int32` ранг (число измерений) | `2` |
| ранг × 4 байта | `int32` размеры по измерениям | `10`, `4` |
| произведение размеров × 4 байта | `float32` значения подряд | 40 нулей (160 байт) |

Итого 4 + (4 + 6 + 4 + 8 + 160) = 186 байт. Формат выведен по одному файлу с одним тензором; порядок элементов многомерных данных (по строкам или по столбцам) и поведение при нескольких тензорах не проверены.

**Ссылка на отсутствующую библиотеку.** В проекте есть `CustomBrick` с `definitionId` `5391938` и `SetVariableBrick` с пользовательской функцией `29481(4, 7)`, но каталога `libs/` и самого `.newlib` в архиве нет. Значит, `.newtrobat` может содержать ссылки на определения из библиотеки, которой в архиве нет (библиотека не обязательна для самого файла). Что при этом делают блоки при выполнении, по файлу не видно: по 6.23 и 6.27 формула без зарегистрированного определения возвращает `0`.

## 8. Источники

Все материалы предоставлены пользователем (кроме общедоступных репозиториев). В колонке «Разделы» указано, где используются данные.

**Официальные ресурсы**

| Источник | Что дал | Разделы |
|---|---|---|
| Репозиторий NewCatroid, https://github.com/Danveyd/NewCatroid | форк Pocket Code, исходный код | весь раздел 6 |
| Репозиторий Catroid, https://github.com/Catrobat/Catroid | родительский проект и формат | 0, 6.12 |
| Страница wiki `newcatroid.mindpy.dev/docs` («Введение», `.mht`) | категории палитры, основные понятия | 6.17 |
| Сырая документация `docs.json` (617 страниц блоков wiki) | описания блоков (отдельный файл `newtrobat_blocks_reference.md`), сверка с классами | 6.18, справочник блоков |

**Исходные файлы (целиком)**

| Файл | Что дал | Разделы |
|---|---|---|
| `Brick.java` | `BrickField`, `BrickData`, `Resources` | 6.1–6.4 |
| `BrickInfo.java` | типы блоков и описания на четырёх языках | 6.5, 6.11 |
| `Sensors.java`, `Functions.java`, `Operators.java`, `InternTokenType.java` | датчики, функции, операторы, токены | 6.7–6.10 |
| `BackwardCompatibleCatrobatLanguageXStream.java` | старый формат и миграции имён | 6.12 |
| `FormulaElement.java` | дерево формул, вычисление функций | 6.13, 6.27 |
| `XStreamBrickConverter.java`, `XStreamFieldKeyOrder.java`, `FormulaBrick.java`, `ApplyShaderBrick.java`, `ShaderBrick.java`, `SetShaderUniformFloatBrick.java`, `SetShaderUniformVec3Brick.java` | запись блока в XML, хранение формул, поля шейдерных блоков | 6.18, 6.19 |
| `LibraryManager.kt`, `CustomBrickManager.kt`, `CustomBrickDefinition.kt` | загрузка библиотек `.newlib`, определения пользовательских блоков | 6.23 |
| Русский `strings.xml` (3761 строка) | названия функций, датчиков, операторов, подписи блоков | 6.11, 6.14–6.16 |

**Выгрузки (результаты `grep`, `sed`, `cat` по проекту)**

| Файл | Что дал | Разделы |
|---|---|---|
| `project-tree.txt` | дерево файлов проекта (классы скриптов и блоков) | 6.11, 6.18 |
| `bricks_fields.txt` | вызовы `addAllowedBrickField` | 6.20 |
| `bricks_data_fields.txt`, `kt_fields.txt` | поля блоков (Java и Kotlin) | 6.21 |
| `xstream_annotations.txt`, `xstreamfieldkeyorder.txt` | аннотации XStream и списки порядка полей | 6.22, 6.30 |
| `libs_refs.txt`, `libs_refs2.txt` | упоминания `libsDir`, `.newlib`, `newtrobat` | 6.23, 6.24 |
| `batch1.txt` | `Constants`, `Project`, `ProjectSecurityChecker`, поля классов модели и скриптов | 6.25, 6.26 |
| `batch2.txt` | алиасы и конвертеры `XstreamSerializer`, `zipProjectWithoutSaves`, `MathFunctionProvider`, `TouchFunctionProvider` | 6.27–6.29 |
| `batch3.txt` | `CatroidFieldKeySorter`, конвертеры, `GroupSprite`, настройки LEGO, версия языка, провайдеры функций | 6.27, 6.30, 6.31 |
| `batch4.txt` | `UserDefinedBrick`, `InputFormulaField`, пути сцен, проверка версии | 6.32, 6.33 |
| `batch5.txt` | `DeviceVariableAccessor`, `DeviceListAccessor`, `loadProject`, `LookData`, кодирование имён, `renameProject`, `setDeviceData` | 6.25, 6.29, 6.33 |

**Реальные файлы**

| Файл | Разделы |
|---|---|
| первый `code.xml` (исходный пример) и второй `code.xml` («Отправка мелких медиа») | 3, 6.6 |
| проект `квадраты тест (FPS) 2.0` | 7.1 |
| проекты `For_Claude_67`, `For_Claude_6752` | 7.2 |
| проект `For_Claude_52` | 7.3 |
| проект `For_Claude_42` | 7.4 |
| проект `Хитрость` | 7.5 |
| проект `PockeTensor+Fast2D (1)` | 7.6 |

**Сведения от пользователя (без файла-источника):** структура архива (`files/`, каталоги сцен), то, что `.newtrobat` это ZIP; актуальная версия приложения 2.2.0 (выпущена 21 июля); «иначе если» и шейдерные экземпляры относятся к версии 2.3.0; блок «При нажатии» срабатывает при нажатии на спрайт; ошибка, из-за которой в NewCatroid нельзя поставить блоки Arduino.
