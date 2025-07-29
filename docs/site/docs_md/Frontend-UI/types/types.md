This file contains all the type definitions for the application.

## Classes

### ApiError

Defined in: [src/types/types.ts:284](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L284)

An error class for API errors.

#### Extends

- [`Error`](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Error)

#### Constructors

##### Constructor

```ts
new ApiError(status, message): ApiError;
```

Defined in: [src/types/types.ts:285](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L285)

###### Parameters

| Parameter | Type     |
| --------- | -------- |
| `status`  | `number` |
| `message` | `string` |

###### Returns

[`ApiError`](#apierror)

###### Overrides

```ts
Error.constructor;
```

#### Properties

| Property                     | Modifier | Type     | Defined in                                                                                                                                      |
| ---------------------------- | -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="status"></a> `status` | `public` | `number` | [src/types/types.ts:285](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L285) |

## Interfaces

### AnkiExportResponse

Defined in: [src/types/types.ts:118](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L118)

The shape of the response from the Anki export endpoint.

#### Properties

| Property                                   | Type     | Defined in                                                                                                                                      |
| ------------------------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="anki_deck_url"></a> `anki_deck_url` | `string` | [src/types/types.ts:119](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L119) |

---

### BreakdownData

Defined in: [src/types/types.ts:108](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L108)

The shape of a breakdown response from the API

#### Properties

| Property                                       | Type                                | Defined in                                                                                                                                      |
| ---------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="focus"></a> `focus`                     | [`BreakdownFocus`](#breakdownfocus) | [src/types/types.ts:110](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L110) |
| <a id="gpt_explanation"></a> `gpt_explanation` | `string`                            | [src/types/types.ts:112](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L112) |
| <a id="sentence"></a> `sentence`               | `string`                            | [src/types/types.ts:109](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L109) |
| <a id="tokens"></a> `tokens`                   | `any`[]                             | [src/types/types.ts:111](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L111) |

---

### BreakdownFocus

Defined in: [src/types/types.ts:97](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L97)

The shape of the focus of a breakdown.

#### Properties

| Property                          | Type       | Defined in                                                                                                                                      |
| --------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="examples"></a> `examples?` | `any`[]    | [src/types/types.ts:102](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L102) |
| <a id="jlpt"></a> `jlpt?`         | `string`   | [src/types/types.ts:101](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L101) |
| <a id="meanings"></a> `meanings`  | `string`[] | [src/types/types.ts:100](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L100) |
| <a id="reading"></a> `reading`    | `string`   | [src/types/types.ts:99](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L99)   |
| <a id="word"></a> `word`          | `string`   | [src/types/types.ts:98](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L98)   |

---

### ChatBubbleProps

Defined in: [src/types/types.ts:251](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L251)

The props for the ChatBubble component.

#### Properties

| Property                               | Type                                      | Defined in                                                                                                                                      |
| -------------------------------------- | ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="msg"></a> `msg`                 | [`Message`](#message)                     | [src/types/types.ts:252](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L252) |
| <a id="onwordclick"></a> `onWordClick` | (`sentence`, `word`) => `void`            | [src/types/types.ts:254](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L254) |
| <a id="tokenizer"></a> `tokenizer`     | `null` \| `Tokenizer`\<`IpadicFeatures`\> | [src/types/types.ts:253](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L253) |

---

### ConvertVideoResponse

Defined in: [src/types/types.ts:66](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L66)

The shape of the response from the convert video endpoint.

#### Properties

| Property                                               | Type     | Defined in                                                                                                                                    |
| ------------------------------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="converted_video_url"></a> `converted_video_url` | `string` | [src/types/types.ts:67](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L67) |

---

### Cue

Defined in: [src/types/types.ts:127](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L127)

The shape of a subtitle cue.

#### Properties

| Property                       | Type               | Defined in                                                                                                                                      |
| ------------------------------ | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="end"></a> `end`         | `number`           | [src/types/types.ts:129](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L129) |
| <a id="raw"></a> `raw`         | `string`           | [src/types/types.ts:131](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L131) |
| <a id="start"></a> `start`     | `number`           | [src/types/types.ts:128](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L128) |
| <a id="tokens-1"></a> `tokens` | `IpadicFeatures`[] | [src/types/types.ts:130](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L130) |

---

### DictLookup

Defined in: [src/types/types.ts:208](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L208)

The shape of all the information from a dictionary lookup as
returned by the API endpoint

#### Properties

| Property                             | Type                        | Defined in                                                                                                                                      |
| ------------------------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="examples-1"></a> `examples`   | `string`[]                  | [src/types/types.ts:215](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L215) |
| <a id="jlpt-1"></a> `jlpt`           | `string`                    | [src/types/types.ts:214](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L214) |
| <a id="jmentries"></a> `jmentries`   | [`JMEntry`](#jmentry)[]     | [src/types/types.ts:210](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L210) |
| <a id="jmnentries"></a> `jmnentries` | [`JMNEntry`](#jmnentry)[]   | [src/types/types.ts:211](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L211) |
| <a id="kanji"></a> `kanji`           | [`KanjiInfo`](#kanjiinfo)[] | [src/types/types.ts:212](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L212) |
| <a id="meanings-1"></a> `meanings`   | `string`[]                  | [src/types/types.ts:213](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L213) |
| <a id="word-1"></a> `word`           | `string`                    | [src/types/types.ts:209](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L209) |

---

### DictWildcardLookup

Defined in: [src/types/types.ts:222](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L222)

The shape of all the information from a wildcard dictionary lookup as
returned by the API endpoint

#### Properties

| Property                               | Type                        | Defined in                                                                                                                                      |
| -------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="examples-2"></a> `examples`     | `string`[]                  | [src/types/types.ts:227](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L227) |
| <a id="jmentries-1"></a> `jmentries`   | [`JMEntry`](#jmentry)[]     | [src/types/types.ts:224](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L224) |
| <a id="jmnentries-1"></a> `jmnentries` | [`JMNEntry`](#jmnentry)[]   | [src/types/types.ts:225](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L225) |
| <a id="kanji-1"></a> `kanji`           | [`KanjiInfo`](#kanjiinfo)[] | [src/types/types.ts:226](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L226) |
| <a id="pattern"></a> `pattern`         | `string`                    | [src/types/types.ts:223](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L223) |

---

### GenerateSrtResponse

Defined in: [src/types/types.ts:59](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L59)

The shape of the response from the generate SRT endpoint.

#### Properties

| Property                               | Type     | Defined in                                                                                                                                    |
| -------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="srt_content"></a> `srt_content` | `string` | [src/types/types.ts:60](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L60) |

---

### GptTemplate

Defined in: [src/types/types.ts:12](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L12)

The shape of a GPT template.

#### Properties

| Property                       | Type     | Defined in                                                                                                                                    |
| ------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="id"></a> `id`           | `string` | [src/types/types.ts:13](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L13) |
| <a id="prompt"></a> `prompt`   | `string` | [src/types/types.ts:15](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L15) |
| <a id="sysmsg"></a> `sysMsg`   | `string` | [src/types/types.ts:14](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L14) |
| <a id="version"></a> `version` | `string` | [src/types/types.ts:16](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L16) |

---

### JMEntry

Defined in: [src/types/types.ts:173](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L173)

The shape of a JMEntry.

#### Properties

| Property                     | Type                        | Defined in                                                                                                                                      |
| ---------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="kana"></a> `kana`     | `string`[]                  | [src/types/types.ts:175](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L175) |
| <a id="kanji-2"></a> `kanji` | `string`[]                  | [src/types/types.ts:176](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L176) |
| <a id="rank"></a> `rank`     | `number`                    | [src/types/types.ts:174](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L174) |
| <a id="senses"></a> `senses` | [`WordSense`](#wordsense)[] | [src/types/types.ts:177](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L177) |

---

### JMNEntry

Defined in: [src/types/types.ts:183](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L183)

The shape of a JMNEntry.

#### Properties

| Property                                         | Type       | Defined in                                                                                                                                      |
| ------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="gloss"></a> `gloss`                       | `string`[] | [src/types/types.ts:187](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L187) |
| <a id="kana-1"></a> `kana`                       | `string`[] | [src/types/types.ts:184](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L184) |
| <a id="kanji-3"></a> `kanji`                     | `string`[] | [src/types/types.ts:185](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L185) |
| <a id="translation_type"></a> `translation_type` | `string`   | [src/types/types.ts:186](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L186) |

---

### KanjiInfo

Defined in: [src/types/types.ts:193](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L193)

The shape of a KANJIDIC2 entry

#### Properties

| Property                                    | Type       | Defined in                                                                                                                                      |
| ------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="grade"></a> `grade?`                 | `number`   | [src/types/types.ts:195](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L195) |
| <a id="jlpt_kanjidic"></a> `jlpt_kanjidic?` | `number`   | [src/types/types.ts:200](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L200) |
| <a id="jlpt_tanos"></a> `jlpt_tanos?`       | `number`   | [src/types/types.ts:201](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L201) |
| <a id="kunyomi"></a> `kunyomi`              | `string`[] | [src/types/types.ts:199](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L199) |
| <a id="literal"></a> `literal`              | `string`   | [src/types/types.ts:194](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L194) |
| <a id="meanings-2"></a> `meanings`          | `string`[] | [src/types/types.ts:197](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L197) |
| <a id="onyomi"></a> `onyomi`                | `string`[] | [src/types/types.ts:198](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L198) |
| <a id="stroke_count"></a> `stroke_count`    | `number`   | [src/types/types.ts:196](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L196) |

---

### Message

Defined in: [src/types/types.ts:235](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L235)

The shape of a message in the transcribe page.

#### Properties

| Property                                        | Type                | Defined in                                                                                                                                      |
| ----------------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="audiourl"></a> `audioUrl?`               | `string`            | [src/types/types.ts:241](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L241) |
| <a id="id-1"></a> `id`                          | `string`            | [src/types/types.ts:236](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L236) |
| <a id="isaudiomessage"></a> `isAudioMessage?`   | `boolean`           | [src/types/types.ts:243](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L243) |
| <a id="isexplanation"></a> `isExplanation?`     | `boolean`           | [src/types/types.ts:244](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L244) |
| <a id="istranscription"></a> `isTranscription?` | `boolean`           | [src/types/types.ts:245](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L245) |
| <a id="loading"></a> `loading?`                 | `boolean`           | [src/types/types.ts:242](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L242) |
| <a id="rawtext"></a> `rawText?`                 | `string`            | [src/types/types.ts:240](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L240) |
| <a id="text"></a> `text?`                       | `string`            | [src/types/types.ts:238](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L238) |
| <a id="tokens-2"></a> `tokens?`                 | `IpadicFeatures`[]  | [src/types/types.ts:239](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L239) |
| <a id="type"></a> `type`                        | `"user"` \| `"bot"` | [src/types/types.ts:237](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L237) |

---

### SaveClipResponse

Defined in: [src/types/types.ts:75](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L75)

The shape of the response from the save clip endpoint.

#### Properties

| Property                         | Type      | Defined in                                                                                                                                    |
| -------------------------------- | --------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="clip_id"></a> `clip_id?`  | `string`  | [src/types/types.ts:78](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L78) |
| <a id="message-1"></a> `message` | `string`  | [src/types/types.ts:77](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L77) |
| <a id="success"></a> `success`   | `boolean` | [src/types/types.ts:76](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L76) |

---

### SettingsDrawerProps

Defined in: [src/types/types.ts:45](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L45)

The props for the SettingsDrawer component.

#### Properties

| Property                                         | Type                                                                | Defined in                                                                                                                                    |
| ------------------------------------------------ | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="onclose"></a> `onClose`                   | () => `void`                                                        | [src/types/types.ts:51](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L51) |
| <a id="onsrt"></a> `onSrt`                       | (`file`) => `void`                                                  | [src/types/types.ts:50](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L50) |
| <a id="ontogglefurigana"></a> `onToggleFurigana` | () => `void`                                                        | [src/types/types.ts:53](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L53) |
| <a id="onvideo"></a> `onVideo`                   | (`file`) => `void`                                                  | [src/types/types.ts:48](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L48) |
| <a id="onvideourl"></a> `onVideoUrl?`            | (`url`) => `void`                                                   | [src/types/types.ts:49](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L49) |
| <a id="showfurigana"></a> `showFurigana`         | `boolean`                                                           | [src/types/types.ts:52](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L52) |
| <a id="srt"></a> `srt`                           | `null` \| [`File`](https://developer.mozilla.org/docs/Web/API/File) | [src/types/types.ts:47](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L47) |
| <a id="video"></a> `video`                       | `null` \| [`File`](https://developer.mozilla.org/docs/Web/API/File) | [src/types/types.ts:46](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L46) |

---

### SubtitlePlayerProps

Defined in: [src/types/types.ts:137](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L137)

The props for the SubtitlePlayer component.

#### Properties

| Property                                   | Type                                                                | Defined in                                                                                                                                      |
| ------------------------------------------ | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="showfurigana-1"></a> `showFurigana` | `boolean`                                                           | [src/types/types.ts:141](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L141) |
| <a id="srt-1"></a> `srt`                   | `null` \| [`File`](https://developer.mozilla.org/docs/Web/API/File) | [src/types/types.ts:140](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L140) |
| <a id="video-1"></a> `video`               | [`File`](https://developer.mozilla.org/docs/Web/API/File)           | [src/types/types.ts:138](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L138) |
| <a id="videourl"></a> `videoUrl?`          | `string`                                                            | [src/types/types.ts:139](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L139) |

---

### SubtitleStyle

Defined in: [src/types/types.ts:270](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L270)

The shape of the subtitle style settings.

#### Properties

| Property                                           | Type     | Defined in                                                                                                                                      |
| -------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="backgroundcolor"></a> `backgroundColor`     | `string` | [src/types/types.ts:273](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L273) |
| <a id="backgroundopacity"></a> `backgroundOpacity` | `number` | [src/types/types.ts:274](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L274) |
| <a id="fontcolor"></a> `fontColor`                 | `string` | [src/types/types.ts:272](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L272) |
| <a id="fontsize"></a> `fontSize`                   | `number` | [src/types/types.ts:271](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L271) |
| <a id="position"></a> `position`                   | `number` | [src/types/types.ts:276](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L276) |
| <a id="textshadow"></a> `textShadow`               | `string` | [src/types/types.ts:275](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L275) |

---

### TranscriptionResponse

Defined in: [src/types/types.ts:260](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L260)

The shape of the response from the transcribe endpoint.

#### Properties

| Property                                          | Type     | Defined in                                                                                                                                      |
| ------------------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="gpt_explanation-1"></a> `gpt_explanation?` | `string` | [src/types/types.ts:262](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L262) |
| <a id="transcript"></a> `transcript`              | `string` | [src/types/types.ts:261](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L261) |

---

### WordDialogProps

Defined in: [src/types/types.ts:149](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L149)

The props for the WordDialog component.

#### Properties

| Property                            | Type                                                                | Defined in                                                                                                                                      |
| ----------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="cueend-1"></a> `cueEnd`      | `number`                                                            | [src/types/types.ts:154](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L154) |
| <a id="cuestart-1"></a> `cueStart`  | `number`                                                            | [src/types/types.ts:153](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L153) |
| <a id="onclose-1"></a> `onClose`    | () => `void`                                                        | [src/types/types.ts:152](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L152) |
| <a id="sentence-1"></a> `sentence`  | `string`                                                            | [src/types/types.ts:150](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L150) |
| <a id="videofile"></a> `videoFile`  | `null` \| [`File`](https://developer.mozilla.org/docs/Web/API/File) | [src/types/types.ts:155](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L155) |
| <a id="videourl-1"></a> `videoUrl?` | `string`                                                            | [src/types/types.ts:156](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L156) |
| <a id="word-2"></a> `word`          | `string`                                                            | [src/types/types.ts:151](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L151) |

---

### WordSense

Defined in: [src/types/types.ts:164](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L164)

The shape of a single sense withing a JMEntry

#### Properties

| Property                     | Type     | Defined in                                                                                                                                      |
| ---------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="gloss-1"></a> `gloss` | `string` | [src/types/types.ts:167](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L167) |
| <a id="order"></a> `order`   | `number` | [src/types/types.ts:165](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L165) |
| <a id="pos"></a> `pos`       | `string` | [src/types/types.ts:166](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L166) |

## Type Aliases

### Clip

```ts
type Clip = object;
```

Defined in: [src/types/types.ts:86](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L86)

The shape of a clip.

#### Properties

| Property                                                        | Type     | Defined in                                                                                                                                    |
| --------------------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="breakdown_response"></a> `breakdown_response`            | `string` | [src/types/types.ts:89](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L89) |
| <a id="get_url"></a> `get_url`                                  | `string` | [src/types/types.ts:88](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L88) |
| <a id="gpt_explanation_preview"></a> `gpt_explanation_preview?` | `string` | [src/types/types.ts:91](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L91) |
| <a id="id-2"></a> `id`                                          | `string` | [src/types/types.ts:87](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L87) |
| <a id="sentence_preview"></a> `sentence_preview?`               | `string` | [src/types/types.ts:90](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L90) |

---

### ProfileFile

```ts
type ProfileFile = object;
```

Defined in: [src/types/types.ts:22](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L22)

The shape of a profile file.

#### Properties

| Property                           | Type     | Defined in                                                                                                                                    |
| ---------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="file_name"></a> `file_name` | `string` | [src/types/types.ts:24](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L24) |
| <a id="file_type"></a> `file_type` | `string` | [src/types/types.ts:26](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L26) |
| <a id="get_url-1"></a> `get_url`   | `string` | [src/types/types.ts:25](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L25) |
| <a id="id-3"></a> `id`             | `string` | [src/types/types.ts:23](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L23) |

---

### ProfileTranscript

```ts
type ProfileTranscript = object;
```

Defined in: [src/types/types.ts:32](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L32)

The shape of a profile transcript.

#### Properties

| Property                                              | Type     | Defined in                                                                                                                                    |
| ----------------------------------------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| <a id="get_url-2"></a> `get_url`                      | `string` | [src/types/types.ts:37](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L37) |
| <a id="gpt_explanation-2"></a> `gpt_explanation?`     | `string` | [src/types/types.ts:36](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L36) |
| <a id="id-4"></a> `id`                                | `string` | [src/types/types.ts:33](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L33) |
| <a id="original_file_name"></a> `original_file_name?` | `string` | [src/types/types.ts:34](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L34) |
| <a id="transcript-1"></a> `transcript`                | `string` | [src/types/types.ts:35](https://github.com/svdC1/mirumoji/blob/40f20ac9954d3b868464cd54b3c6b759a654ba9a/apps/frontend/src/types/types.ts#L35) |
