#!/usr/bin/env python3
"""
Generate a realistic bethune-project workspace simulating an existing Flink Kafka monitoring repo.
The agent must read the existing pattern files and generate a new task (task 37) from scratch.
"""

import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "src/main/java/com/ly/tms/job",
    "src/main/java/com/ly/tms/po/carSupply",
    "src/main/java/com/ly/tms/util",
    "src/main/java/com/ly/tms/sink",
    "src/main/resources",
    "src/main/resources/dev",
    "src/main/resources/product",
    "src/main/resources/stage",
    "src/test/java/com/ly/tms",
    "references",
    "docs/archive",
    "scripts",
    "target/classes",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)


# ─── Helper to write files ──────────────────────────────────────────────────────
def write(path, content):
    full = os.path.join(WORKSPACE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(textwrap.dedent(content))


# ─── REFERENCE: Task 34 MessageModel ──────────────────────────────────────────
write("src/main/java/com/ly/tms/po/carSupply/SkynetLogReplacePriceMessageModel.java", """\
package com.ly.tms.po.carSupply;

import com.alibaba.fastjson.annotation.JSONField;
import lombok.Data;

@Data
public class SkynetLogReplacePriceMessageModel {

    private String apmtraceid;
    private String id;
    private String logTime;
    private String module;
    private String traceid;
    private SkyNetVo skyNetVo;

    @Data
    public static class SkyNetVo {
        private String id;
        @JSONField(name = "refer_price")
        private String referPrice;
        @JSONField(name = "replace_price")
        private String replacePrice;
        private String routeId;
        private String deptDate;
    }
}
""")

# ─── REFERENCE: Task 34 Po ────────────────────────────────────────────────────
write("src/main/java/com/ly/tms/po/carSupply/SkynetLogReplacePricePo.java", """\
package com.ly.tms.po.carSupply;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class SkynetLogReplacePricePo {

    private LocalDateTime st;
    private String apmtraceid;
    private String id;
    private Integer cnt;
    private String traceid;
    private String referPrice;
    private String replacePrice;
    private String routeId;
    private String deptDate;
    private String year;
    private String month;
    private String day;
}
""")

# ─── REFERENCE: Task 34 Job ──────────────────────────────────────────────────
write("src/main/java/com/ly/tms/job/Bus_Search_ReplacePrice_KafkaToStarRock_34.java", """\
package com.ly.tms.job;

import com.alibaba.fastjson.JSON;
import com.ly.tms.po.carSupply.SkynetLogReplacePriceMessageModel;
import com.ly.tms.po.carSupply.SkynetLogReplacePricePo;
import com.ly.tms.util.DateUtil;
import com.ly.tms.util.SafeUtil;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDateTime;
import java.util.UUID;

public class Bus_Search_ReplacePrice_KafkaToStarRock_34 {

    private static final Logger LOG = LoggerFactory.getLogger(Bus_Search_ReplacePrice_KafkaToStarRock_34.class);
    private static final String MODULE = "BUS_Public_SFC_Replace_Price_Monitor";

    public static void main(String[] args) throws Exception {
        // env setup, kafka source, etc. (omitted for brevity)
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        // ... kafka source wired to process()
        env.execute("Bus_Search_ReplacePrice_KafkaToStarRock_34");
    }

    public static SkynetLogReplacePricePo process(String raw) {
        if (raw == null || raw.trim().isEmpty()) return null;
        SkynetLogReplacePriceMessageModel model;
        try {
            model = JSON.parseObject(raw, SkynetLogReplacePriceMessageModel.class);
        } catch (Exception e) {
            LOG.error("parse error", e);
            return null;
        }
        if (model.getMessage() == null || model.getMessage().trim().isEmpty()) return null;
        if (!MODULE.equals(model.getModule())) return null;

        String logTimeStr = model.getLogTime();
        LocalDateTime st;
        try {
            st = DateUtil.parseAndFormatLogTime(logTimeStr);
            if (st == null) throw new RuntimeException("null result");
        } catch (Exception e) {
            LOG.error("logTime parse failed: {}", logTimeStr, e);
            return null;
        }

        SkynetLogReplacePricePo po = new SkynetLogReplacePricePo();
        po.setSt(st);
        po.setApmtraceid(SafeUtil.safe(model.getApmtraceid()));
        String id = (model.getSkyNetVo() != null && model.getSkyNetVo().getId() != null)
                ? model.getSkyNetVo().getId()
                : UUID.randomUUID().toString();
        po.setId(id);
        po.setCnt(1);
        po.setTraceid(SafeUtil.safe(model.getTraceid()));
        SkynetLogReplacePriceMessageModel.SkyNetVo vo = model.getSkyNetVo();
        po.setReferPrice(SafeUtil.safe(vo != null ? vo.getReferPrice() : null));
        po.setReplacePrice(SafeUtil.safe(vo != null ? vo.getReplacePrice() : null));
        po.setRouteId(SafeUtil.safe(vo != null ? vo.getRouteId() : null));
        po.setDeptDate(SafeUtil.safe(vo != null ? vo.getDeptDate() : null));

        po.setYear(String.valueOf(st.getYear()));
        po.setMonth(String.format("%02d", st.getMonthValue()));
        po.setDay(String.format("%02d", st.getDayOfMonth()));
        return po;
    }
}
""")

# ─── REFERENCE: Task 35 Job (list-expansion pattern) ────────────────────────
write("src/main/java/com/ly/tms/job/Bus_Carpool_CalEnter_KafkaToStarRock_35.java", """\
package com.ly.tms.job;

import com.alibaba.fastjson.JSON;
import com.ly.tms.po.carSupply.SkynetLogCalEnterMessageModel;
import com.ly.tms.po.carSupply.SkynetLogCalEnterPo;
import com.ly.tms.util.DateUtil;
import com.ly.tms.util.SafeUtil;
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public class Bus_Carpool_CalEnter_KafkaToStarRock_35 {

    private static final Logger LOG = LoggerFactory.getLogger(Bus_Carpool_CalEnter_KafkaToStarRock_35.class);
    private static final String MODULE = "BUS_PUBLIC_CARPOOL_PRICING_CallEnter";

    public static class ProcessFlatMap implements FlatMapFunction<String, SkynetLogCalEnterPo> {
        @Override
        public void flatMap(String raw, Collector<SkynetLogCalEnterPo> out) {
            if (raw == null || raw.trim().isEmpty()) return;
            SkynetLogCalEnterMessageModel model;
            try {
                model = JSON.parseObject(raw, SkynetLogCalEnterMessageModel.class);
            } catch (Exception e) {
                LOG.error("parse error", e);
                return;
            }
            if (model.getMessage() == null || model.getMessage().trim().isEmpty()) return;
            if (!MODULE.equals(model.getModule())) return;

            String logTimeStr = model.getLogTime();
            LocalDateTime st;
            try {
                st = DateUtil.parseAndFormatLogTime(logTimeStr);
                if (st == null) throw new RuntimeException("null");
            } catch (Exception e) {
                LOG.error("logTime parse failed: {}", logTimeStr, e);
                return;
            }

            List<SkynetLogCalEnterMessageModel.FullPriceItem> list = null;
            if (model.getSkyNetVo() != null) list = model.getSkyNetVo().getFullPriceList();
            if (list == null || list.isEmpty()) return;

            for (SkynetLogCalEnterMessageModel.FullPriceItem item : list) {
                SkynetLogCalEnterPo po = new SkynetLogCalEnterPo();
                po.setSt(st);
                po.setApmtraceid(SafeUtil.safe(model.getApmtraceid()));
                String id = (model.getSkyNetVo() != null && model.getSkyNetVo().getId() != null)
                        ? model.getSkyNetVo().getId()
                        : UUID.randomUUID().toString();
                po.setId(id);
                po.setCnt(1);
                po.setTraceid(SafeUtil.safe(model.getTraceid()));
                po.setRouteId(SafeUtil.safe(item.getRouteId()));
                po.setSegmentPrice(item.getSegmentPrice());
                po.setYear(String.valueOf(st.getYear()));
                po.setMonth(String.format("%02d", st.getMonthValue()));
                po.setDay(String.format("%02d", st.getDayOfMonth()));
                out.collect(po);
            }
        }
    }
}
""")

# ─── REFERENCE: Task 36 Job (datas list-expansion pattern) ─────────────────
write("src/main/java/com/ly/tms/job/Bus_Metric_Collection_KafkaToStarRock_36.java", """\
package com.ly.tms.job;

import com.alibaba.fastjson.JSON;
import com.ly.tms.po.carSupply.SkynetLogMetricCollectionMessageModel;
import com.ly.tms.po.carSupply.SkynetLogMetricCollectionPo;
import com.ly.tms.util.DateUtil;
import com.ly.tms.util.SafeUtil;
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.util.Collector;
import org.slf4j.Logger;import org.slf4j.LoggerFactory;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public class Bus_Metric_Collection_KafkaToStarRock_36 {

    private static final Logger LOG = LoggerFactory.getLogger(Bus_Metric_Collection_KafkaToStarRock_36.class);
    private static final String MODULE = "BUS_METRIC_COLLECTION";

    public static class ProcessFlatMap implements FlatMapFunction<String, SkynetLogMetricCollectionPo> {
        @Override
        public void flatMap(String raw, Collector<SkynetLogMetricCollectionPo> out) {
            if (raw == null || raw.trim().isEmpty()) return;
            SkynetLogMetricCollectionMessageModel model;
            try {
                model = JSON.parseObject(raw, SkynetLogMetricCollectionMessageModel.class);
            } catch (Exception e) { LOG.error("parse error", e); return; }
            if (model.getMessage() == null || model.getMessage().trim().isEmpty()) return;
            if (!MODULE.equals(model.getModule())) return;

            String logTimeStr = model.getLogTime();
            LocalDateTime st;
            try {
                st = DateUtil.parseAndFormatLogTime(logTimeStr);
                if (st == null) throw new RuntimeException("null");
            } catch (Exception e) { LOG.error("logTime parse failed: {}", logTimeStr, e); return; }

            List<SkynetLogMetricCollectionMessageModel.DataItem> datas = null;
            if (model.getSkyNetVo() != null) datas = model.getSkyNetVo().getDatas();
            if (datas == null || datas.isEmpty()) return;

            for (SkynetLogMetricCollectionMessageModel.DataItem item : datas) {
                SkynetLogMetricCollectionPo po = new SkynetLogMetricCollectionPo();
                po.setSt(st);
                po.setApmtraceid(SafeUtil.safe(model.getApmtraceid()));
                String id = (model.getSkyNetVo() != null && model.getSkyNetVo().getId() != null)
                        ? model.getSkyNetVo().getId() : UUID.randomUUID().toString();
                po.setId(id);
                po.setCnt(1);
                po.setTraceid(SafeUtil.safe(model.getTraceid()));
                po.setMetricKey(SafeUtil.safe(item.getMetricKey()));
                po.setMetricValue(item.getMetricValue());
                po.setYear(String.valueOf(st.getYear()));
                po.setMonth(String.format("%02d", st.getMonthValue()));
                po.setDay(String.format("%02d", st.getDayOfMonth()));
                out.collect(po);
            }
        }
    }
}
""")

# ─── REFERENCE: Task 33 Job (simple single-row, no nested list) ────────────
write("src/main/java/com/ly/tms/job/Bus_Search_Abtest_KafkaToStarRock_33.java", """\
package com.ly.tms.job;

import com.alibaba.fastjson.JSON;
import com.ly.tms.po.carSupply.SkynetLogAbtestMessageModel;
import com.ly.tms.po.carSupply.SkynetLogAbtestPo;
import com.ly.tms.util.DateUtil;
import com.ly.tms.util.SafeUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.time.LocalDateTime;
import java.util.UUID;

public class Bus_Search_Abtest_KafkaToStarRock_33 {

    private static final Logger LOG = LoggerFactory.getLogger(Bus_Search_Abtest_KafkaToStarRock_33.class);
    private static final String MODULE = "BUS_Public_SFC_ABTest_Monitor";

    public static SkynetLogAbtestPo process(String raw) {
        if (raw == null || raw.trim().isEmpty()) return null;
        SkynetLogAbtestMessageModel model;
        try {
            model = JSON.parseObject(raw, SkynetLogAbtestMessageModel.class);
        } catch (Exception e) { LOG.error("parse error", e); return null; }
        if (model.getMessage() == null || model.getMessage().trim().isEmpty()) return null;
        if (!MODULE.equals(model.getModule())) return null;

        LocalDateTime st;
        try {
            st = DateUtil.parseAndFormatLogTime(model.getLogTime());
            if (st == null) throw new RuntimeException("null");
        } catch (Exception e) { LOG.error("logTime parse failed: {}", model.getLogTime(), e); return null; }

        SkynetLogAbtestPo po = new SkynetLogAbtestPo();
        po.setSt(st);
        po.setApmtraceid(SafeUtil.safe(model.getApmtraceid()));
        String id = (model.getSkyNetVo() != null && model.getSkyNetVo().getId() != null)
                ? model.getSkyNetVo().getId() : UUID.randomUUID().toString();
        po.setId(id);
        po.setCnt(1);
        po.setTraceid(SafeUtil.safe(model.getTraceid()));
        po.setAbGroup(SafeUtil.safe(model.getSkyNetVo() != null ? model.getSkyNetVo().getAbGroup() : null));
        po.setYear(String.valueOf(st.getYear()));
        po.setMonth(String.format("%02d", st.getMonthValue()));
        po.setDay(String.format("%02d", st.getDayOfMonth()));
        return po;
    }
}
""")

# ─── Existing PO/MessageModel stubs for tasks 33/35/36 ──────────────────────
write("src/main/java/com/ly/tms/po/carSupply/SkynetLogAbtestMessageModel.java", """\
package com.ly.tms.po.carSupply;
import lombok.Data;
@Data
public class SkynetLogAbtestMessageModel {
    private String apmtraceid;
    private String id;
    private String logTime;
    private String message;
    private String module;
    private String traceid;
    private SkyNetVo skyNetVo;
    @Data
    public static class SkyNetVo {
        private String id;
        private String abGroup;
    }
}
""")

write("src/main/java/com/ly/tms/po/carSupply/SkynetLogAbtestPo.java", """\
package com.ly.tms.po.carSupply;
import lombok.Data;
import java.time.LocalDateTime;
@Data
public class SkynetLogAbtestPo {
    private LocalDateTime st;
    private String apmtraceid;
    private String id;
    private Integer cnt;
    private String traceid;
    private String abGroup;
    private String year;
    private String month;
    private String day;
}
""")

write("src/main/java/com/ly/tms/po/carSupply/SkynetLogCalEnterMessageModel.java", """\
package com.ly.tms.po.carSupply;
import lombok.Data;
import java.util.List;
@Data
public class SkynetLogCalEnterMessageModel {
    private String apmtraceid;
    private String id;
    private String logTime;
    private String message;
    private String module;
    private String traceid;
    private SkyNetVo skyNetVo;
    @Data
    public static class SkyNetVo {
        private String id;
        private List<FullPriceItem> fullPriceList;
    }
    @Data
    public static class FullPriceItem {
        private String routeId;
        private Double segmentPrice;
    }
}
""")

write("src/main/java/com/ly/tms/po/carSupply/SkynetLogCalEnterPo.java", """\
package com.ly.tms.po.carSupply;
import lombok.Data;
import java.time.LocalDateTime;
@Data
public class SkynetLogCalEnterPo {
    private LocalDateTime st;
    private String apmtraceid;
    private String id;
    private Integer cnt;
    private String traceid;
    private String routeId;
    private Double segmentPrice;
    private String year;
    private String month;
    private String day;
}
""")

write("src/main/java/com/ly/tms/po/carSupply/SkynetLogMetricCollectionMessageModel.java", """\
package com.ly.tms.po.carSupply;
import lombok.Data;
import java.util.List;
@Data
public class SkynetLogMetricCollectionMessageModel {
    private String apmtraceid;
    private String id;
    private String logTime;
    private String message;
    private String module;
    private String traceid;
    private SkyNetVo skyNetVo;
    @Data
    public static class SkyNetVo {
        private String id;
        private List<DataItem> datas;
    }
    @Data
    public static class DataItem {
        private String metricKey;
        private Double metricValue;
    }
}
""")

write("src/main/java/com/ly/tms/po/carSupply/SkynetLogMetricCollectionPo.java", """\
package com.ly.tms.po.carSupply;
import lombok.Data;
import java.time.LocalDateTime;
@Data
public class SkynetLogMetricCollectionPo {
    private LocalDateTime st;
    private String apmtraceid;
    private String id;
    private Integer cnt;
    private String traceid;
    private String metricKey;
    private Double metricValue;
    private String year;
    private String month;
    private String day;
}
""")

# ─── Utility stubs ───────────────────────────────────────────────────────────
write("src/main/java/com/ly/tms/util/DateUtil.java", """\
package com.ly.tms.util;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
public class DateUtil {
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    public static LocalDateTime parseAndFormatLogTime(String s) {
        if (s == null || s.trim().isEmpty()) return null;
        return LocalDateTime.parse(s.trim(), FMT);
    }
}
""")

write("src/main/java/com/ly/tms/util/SafeUtil.java", """\
package com.ly.tms.util;
public class SafeUtil {
    public static String safe(String s) {
        return s == null ? "" : s.trim();
    }
}
""")

write("src/main/java/com/ly/tms/sink/StarRocksSinkBuilder.java", """\
package com.ly.tms.sink;
// Generic StarRocks sink builder - each job implements StarRocksSinkRowBuilder inline
public class StarRocksSinkBuilder {}
""")

# ─── EXISTING 4 config.properties files ────────────────────────────────────
CONFIG_COMMON = """\
# Bethune Flink Job Configuration
# ======== Kafka Bus Search ========
kafka.bus.abtest.topic=skynet_log_Public_SFC_ABTest_Monitor
kafka.bus.replacePrice.topic=skynet_log_Public_SFC_Replace_Price_Monitor

# ======== Kafka Bus Carpool ========
kafka.bus.calenter.topic=skynet_log_3304590_CallEnter

# ======== Kafka Bus Metric ========
kafka.bus.metricCollection.topic=skynet_log_3309435_bus_travelmetrics

# ======== Consumer Groups ========
travel.car.abtest.group=flink_consumer_abtest_group
travel.car.replacePrice.group=flink_consumer_replacePrice_group
travel.car.calenter.group=flink_consumer_calenter_group
travel.car.metricCollection.group=flink_consumer_metricCollection_group

# ======== StarRocks Tables ========
starrocks.fe.travel.common.abtestMonitor=bus_sfc_abtest_monitor
starrocks.fe.travel.common.replacePriceMonitor=bus_sfc_replace_price_monitor
starrocks.fe.travel.common.calenterMonitor=bus_carpool_calenter_monitor
starrocks.fe.travel.common.metricCollectionMonitor=bus_metric_collection_monitor

# ======== Hive Tables ========
hive.hive_train_ops.abtestMonitor=bus_sfc_abtest_monitor
hive.hive_train_ops.replacePriceMonitor=bus_sfc_replace_price_monitor
hive.hive_train_ops.calenterMonitor=bus_carpool_calenter_monitor
hive.hive_train_ops.metricCollectionMonitor=bus_metric_collection_monitor

# ======== StarRocks FE ========
starrocks.fe.http.url=http://starrocks-fe:8030
starrocks.fe.jdbc.url=jdbc:mysql://starrocks-fe:9030
starrocks.fe.user=root
starrocks.fe.password=

# ======== Hive Metastore ========
hive.metastore.uris=thrift://hive-meta:9083
"""

for cfg_path in [
    "src/main/resources/config.properties",
    "src/main/resources/dev/config.properties",
    "src/main/resources/product/config.properties",
    "src/main/resources/stage/config.properties",
]:
    write(cfg_path, CONFIG_COMMON)

# ─── bethune-patterns.md reference ──────────────────────────────────────────
write("references/bethune-patterns.md", """\
# Bethune Flink Kafka Task Patterns

## Task Pattern Comparison

| Aspect | Task 33 | Task 34 | Task 35 | Task 36 |
|--------|---------|---------|---------|---------|
| Output mode | single-row | single-row (nested VO) | list expand (fullPriceList) | list expand (datas) |
| FlatMap? | No (map) | No (map) | Yes | Yes |
| List null guard | N/A | N/A | return if null/empty | return if null/empty |
| Id source | skyNetVo.getId() / UUID | skyNetVo.getId() / UUID | skyNetVo.getId() / UUID | skyNetVo.getId() / UUID |
| logTime handling | A: log error + discard | A: log error + discard | A: log error + discard | A: log error + discard |

## Fixed Field Ordering Rules

The following order MUST be consistent across TableSchema, StarRocksSinkRowBuilder, AND toHiveRow():

1. st (always first)
2. apmtraceid
3. id
4. cnt
5. traceid
6. [business fields in PO declaration order]

Hive toHiveRow() MUST append: year, month, day as last three elements.

## parseAndFormatLogTime() contract

```java
// A-scheme: empty or parse failure -> LOG.error + return null (caller discards)
LocalDateTime st;
try {
    st = DateUtil.parseAndFormatLogTime(logTimeStr);
    if (st == null) throw new RuntimeException("null result");
} catch (Exception e) {
    LOG.error("logTime parse failed: {}", logTimeStr, e);
    return null;  // or: return (from flatMap)
}
```

## toHiveRow() fixed template

```java
public Object[] toHiveRow() {
    return new Object[]{
        st, apmtraceid, id, cnt, traceid,
        /* business fields */,
        year, month, day   // ALWAYS last three
    };
}
```

## Config insertion groups

- Kafka topics: under `# ======== Kafka Bus {Section} ========`
- Consumer groups: under `# ======== Consumer Groups ========`
- StarRocks tables: under `# ======== StarRocks Tables ========`
- Hive tables: under `# ======== Hive Tables ========`

## Config key naming

- topic: kafka.bus.{camelBizName}.topic
- group: travel.car.{camelBizName}.group
- starrocks: starrocks.fe.travel.common.{camelBizName}Monitor
- hive: hive.hive_train_ops.{camelBizName}Monitor
""")

# ─── Distractor files ────────────────────────────────────────────────────────
write("docs/archive/task_32_deprecated.md", """\
# Task 32 - Deprecated
This task was removed in Q2 2023. Do not reference.
topic: skynet_log_old_task32
module: BUS_DEPRECATED_32
""")

write("docs/archive/migration_notes.txt", """\
Migration from Flink 1.12 to 1.16 completed 2023-09.
All jobs use new KafkaSource API.
StarRocks sink upgraded to 3.x connector.
""")

write("scripts/deploy.sh", """\
#!/bin/bash
# Deployment script - not relevant to task generation
mvn clean package -DskipTests
scp target/*.jar deploy@prod-cluster:/opt/flink/jobs/
""")

write("scripts/create_tables.sql", """\
-- Placeholder DDL for existing tables
-- DO NOT MODIFY existing tables
CREATE TABLE IF NOT EXISTS TCTravelStreamData_db.bus_sfc_abtest_monitor (
    st DATETIME, apmtraceid VARCHAR(256), id VARCHAR(256), cnt INT,
    traceid VARCHAR(256), ab_group VARCHAR(512)
) DUPLICATE KEY(st, apmtraceid) DISTRIBUTED BY HASH(id) BUCKETS 8;
""")

write("src/test/java/com/ly/tms/DateUtilTest.java", """\
package com.ly.tms;
import org.junit.Test;
public class DateUtilTest {
    @Test
    public void testParse() { /* unit tests */ }
}
""")

write("target/classes/.gitkeep", "")

write("src/main/java/com/ly/tms/sink/HiveSinkBuilder.java", """\
package com.ly.tms.sink;
public class HiveSinkBuilder {
    // Connects to Hive using toHiveRow() output
}
""")

write("src/main/java/com/ly/tms/util/ConfigLoader.java", """\
package com.ly.tms.util;
import java.util.Properties;
public class ConfigLoader {
    public static Properties load(String env) throws Exception {
        Properties p = new Properties();
        String path = env.isEmpty() ? "config.properties" : env + "/config.properties";
        p.load(ConfigLoader.class.getClassLoader().getResourceAsStream(path));
        return p;
    }
}
""")

# ─── pom.xml (minimal, for Maven structure recognition) ─────────────────────
write("pom.xml", """\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.ly.tms</groupId>
    <artifactId>bethune</artifactId>
    <version>1.0-SNAPSHOT</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.apache.flink</groupId>
            <artifactId>flink-streaming-java</artifactId>
            <version>1.16.0</version>
        </dependency>
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>fastjson</artifactId>
            <version>1.2.83</version>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <version>1.18.26</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.slf4j</groupId>
            <artifactId>slf4j-api</artifactId>
            <version>1.7.36</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(WORKSPACE):
    for f in files:
        rel = os.path.relpath(os.path.join(root, f), WORKSPACE)
        print(f"  {rel}")