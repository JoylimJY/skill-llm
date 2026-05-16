import os
import random
random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "src/main/java/com/ecommerce/order/dal/mysql/mapper",
    "src/main/java/com/ecommerce/order/dal/mysql/entity",
    "src/main/java/com/ecommerce/order/service/impl",
    "src/main/java/com/ecommerce/order/controller",
    "src/main/java/com/ecommerce/order/config",
    "src/main/resources/mapper",
    "src/main/resources",
    "src/test/java/com/ecommerce/order",
    "docs",
    "scripts",
    "target/classes",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── Distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "docs/architecture.md": "# Architecture\nThis service handles order processing.\nSee confluence for details.",
    "docs/api-spec.yaml": "openapi: '3.0'\ninfo:\n  title: Order API\n  version: '1.0'",
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying order service...'\nkubectl apply -f k8s/",
    "scripts/backup_db.sh": "#!/bin/bash\nmysqldump -u root orderdb > backup.sql",
    "src/test/java/com/ecommerce/order/OrderServiceTest.java": """\
package com.ecommerce.order;
import org.junit.jupiter.api.Test;
public class OrderServiceTest {
    @Test
    public void testPlaceOrder() { /* TODO */ }
}
""",
    "src/main/java/com/ecommerce/order/controller/OrderController.java": """\
package com.ecommerce.order.controller;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    // order endpoints
}
""",
    "src/main/java/com/ecommerce/order/service/impl/OrderServiceImpl.java": """\
package com.ecommerce.order.service.impl;
import org.springframework.stereotype.Service;
@Service
public class OrderServiceImpl {
    // business logic
}
""",
    "src/main/java/com/ecommerce/order/config/SecurityConfig.java": """\
package com.ecommerce.order.config;
import org.springframework.context.annotation.Configuration;
@Configuration
public class SecurityConfig {
    // security settings
}
""",
    "src/main/java/com/ecommerce/order/dal/mysql/entity/OrderDO.java": """\
package com.ecommerce.order.dal.mysql.entity;
import com.baomidou.mybatisplus.annotation.*;
@KeySequence("order_seq")
@TableName("orders")
public class OrderDO {
    @TableId(type = IdType.INPUT)
    private Long id;
    private String userName;
    private Integer status;
    private java.math.BigDecimal totalAmount;
    // getters/setters omitted
}
""",
    "src/main/java/com/ecommerce/order/dal/mysql/entity/OrderDetailDO.java": """\
package com.ecommerce.order.dal.mysql.entity;
import com.baomidou.mybatisplus.annotation.*;
@KeySequence("order_detail_seq")
@TableName("order_detail")
public class OrderDetailDO {
    @TableId(type = IdType.INPUT)
    private Long id;
    private Long orderId;
    private String productName;
    private Integer quantity;
    private java.math.BigDecimal price;
    private Integer flagCol;
    private Integer statusCol;
    // getters/setters omitted
}
""",
    "target/classes/.gitkeep": "",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ─── application.yaml (MySQL config, needs migration) ─────────────────────────
application_yaml = """\
spring:
  application:
    name: order-service
  datasource:
    url: jdbc:mysql://db-host:3306/orderdb
    username: appuser
    password: s3cr3t
    driver-class-name: com.mysql.cj.jdbc.Driver
    hikari:
      connection-test-query: SELECT 1 FROM DUAL
      maximum-pool-size: 20

mybatis-plus:
  mapper-locations: classpath*:mapper/*.xml
  global-config:
    db-config:
      logic-delete-field: deleted
      logic-delete-value: 1
      logic-not-delete-value: 0
  configuration:
    map-underscore-to-camel-case: true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl

logging:
  level:
    com.ecommerce.order.dal.mysql.mapper: DEBUG

server:
  port: 8080
"""
with open(os.path.join(workspace, "src/main/resources/application.yaml"), "w") as f:
    f.write(application_yaml)

# ─── OrderMapper.xml (main mapper, many MySQL-isms) ───────────────────────────
order_mapper_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.ecommerce.order.dal.mysql.mapper.OrderMapper">

    <resultMap id="OrderResultMap" type="com.ecommerce.order.dal.mysql.entity.OrderDO">
        <id column="id" property="id"/>
        <result column="user_name" property="userName"/>
        <result column="status" property="status"/>
        <result column="total_amount" property="totalAmount"/>
    </resultMap>

    <!-- Query active orders with formatted date -->
    <select id="selectActiveOrders" resultMap="OrderResultMap">
        SELECT id,
               user_name,
               status,
               total_amount,
               DATE_FORMAT(create_time, '%Y-%m-%d') AS create_date
        FROM orders
        WHERE deleted = 0
          AND status = 1
          AND create_time &gt;= DATE_ADD(CURDATE(), INTERVAL -30 DAY)
    </select>

    <!-- Query orders with IFNULL fallback -->
    <select id="selectOrdersWithFallback" resultType="map">
        SELECT id,
               IFNULL(remark, '无备注') AS remark,
               IFNULL(coupon_code, 'N/A') AS coupon_code
        FROM orders
        WHERE deleted = 0
    </select>

    <!-- Insert or ignore duplicate order -->
    <insert id="insertIgnoreOrder">
        INSERT IGNORE INTO orders (id, user_name, status, total_amount, create_time)
        VALUES (#{id}, #{userName}, #{status}, #{totalAmount}, NOW())
    </insert>

    <!-- Upsert order status -->
    <insert id="upsertOrderStatus">
        INSERT INTO orders (id, status, update_time)
        VALUES (#{id}, #{status}, NOW())
        ON DUPLICATE KEY UPDATE
            status = #{status},
            update_time = NOW()
    </insert>

    <!-- Update user name from user table via JOIN -->
    <update id="syncUserNameFromUserTable">
        UPDATE orders o
        INNER JOIN users u ON o.user_id = u.id
        SET o.user_name = u.name,
            o.update_time = NOW()
        WHERE o.deleted = 0
          AND o.status = 1
    </update>

    <!-- Soft delete -->
    <update id="softDeleteOrder">
        UPDATE orders
        SET deleted = 1,
            update_time = NOW()
        WHERE id = #{id}
          AND deleted = 0
    </update>

    <!-- Cast datetime field -->
    <select id="selectByDateRange" resultType="map">
        SELECT id,
               user_name,
               CAST(create_time AS DATETIME) AS order_datetime,
               DATE(create_time) AS order_date
        FROM orders
        WHERE deleted = 0
          AND CAST(create_time AS DATETIME) &gt;= #{startTime}
    </select>

</mapper>
"""
with open(os.path.join(workspace, "src/main/resources/mapper/OrderMapper.xml"), "w") as f:
    f.write(order_mapper_xml)

# ─── OrderDetailMapper.xml (GROUP BY + BIT issues) ────────────────────────────
order_detail_mapper_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
        "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.ecommerce.order.dal.mysql.mapper.OrderDetailMapper">

    <resultMap id="DetailResultMap" type="com.ecommerce.order.dal.mysql.entity.OrderDetailDO">
        <id column="id" property="id"/>
        <result column="order_id" property="orderId"/>
        <result column="product_name" property="productName"/>
        <result column="quantity" property="quantity"/>
        <result column="price" property="price"/>
        <result column="flag_col" property="flagCol"/>
        <result column="status_col" property="statusCol"/>
    </resultMap>

    <!-- GROUP BY query - MySQL lenient mode, will fail in PG -->
    <select id="selectOrderSummary" resultType="map">
        SELECT o.id,
               d.flag_col,
               d.status_col,
               MIN(d.price) AS min_price,
               SUM(d.quantity) AS total_qty
        FROM orders o
        LEFT JOIN order_detail d ON o.id = d.order_id
        WHERE o.deleted = 0
        GROUP BY o.id
    </select>

    <!-- Active detail with BIT comparison -->
    <select id="selectActiveDetails" resultType="map">
        SELECT id, order_id, product_name, quantity, price
        FROM order_detail
        WHERE deleted = 0
          AND flag_col = 1
    </select>

    <!-- Insert detail or ignore -->
    <insert id="insertIgnoreDetail">
        INSERT IGNORE INTO order_detail (id, order_id, product_name, quantity, price, flag_col)
        VALUES (#{id}, #{orderId}, #{productName}, #{quantity}, #{price}, #{flagCol})
    </insert>

    <!-- Update detail prices from product catalog via JOIN -->
    <update id="syncPricesFromCatalog">
        UPDATE order_detail d
        INNER JOIN product p ON d.product_id = p.id
        SET d.price = p.current_price,
            d.update_time = NOW()
        WHERE d.deleted = 0
    </update>

    <!-- Soft delete detail -->
    <update id="softDeleteDetail">
        UPDATE order_detail
        SET deleted = 1
        WHERE order_id = #{orderId}
          AND deleted = 0
    </update>

</mapper>
"""
with open(os.path.join(workspace, "src/main/resources/mapper/OrderDetailMapper.xml"), "w") as f:
    f.write(order_detail_mapper_xml)

# ─── max_id_reference.txt: simulates a DB export showing current max IDs ──────
max_id_reference = """\
# Current maximum IDs in production database (exported before migration)
# Use these values to set SEQUENCE start points
orders.max_id=10500
order_detail.max_id=87300
"""
with open(os.path.join(workspace, "scripts/max_id_reference.txt"), "w") as f:
    f.write(max_id_reference)

# ─── OrderMapper.java stub ────────────────────────────────────────────────────
order_mapper_java = """\
package com.ecommerce.order.dal.mysql.mapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ecommerce.order.dal.mysql.entity.OrderDO;
import org.apache.ibatis.annotations.Mapper;
import java.util.List;
import java.util.Map;
@Mapper
public interface OrderMapper extends BaseMapper<OrderDO> {
    List<Map<String, Object>> selectActiveOrders();
    List<Map<String, Object>> selectOrdersWithFallback();
    void insertIgnoreOrder(OrderDO order);
    void upsertOrderStatus(OrderDO order);
    void syncUserNameFromUserTable();
    void softDeleteOrder(Long id);
    List<Map<String, Object>> selectByDateRange(String startTime);
}
"""
with open(os.path.join(workspace, "src/main/java/com/ecommerce/order/dal/mysql/mapper/OrderMapper.java"), "w") as f:
    f.write(order_mapper_java)

order_detail_mapper_java = """\
package com.ecommerce.order.dal.mysql.mapper;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ecommerce.order.dal.mysql.entity.OrderDetailDO;
import org.apache.ibatis.annotations.Mapper;
import java.util.List;
import java.util.Map;
@Mapper
public interface OrderDetailMapper extends BaseMapper<OrderDetailDO> {
    List<Map<String, Object>> selectOrderSummary();
    List<Map<String, Object>> selectActiveDetails();
    void insertIgnoreDetail(OrderDetailDO detail);
    void syncPricesFromCatalog();
    void softDeleteDetail(Long orderId);
}
"""
with open(os.path.join(workspace, "src/main/java/com/ecommerce/order/dal/mysql/mapper/OrderDetailMapper.java"), "w") as f:
    f.write(order_detail_mapper_java)

print("Workspace generated successfully.")
print(f"Files created under: {workspace}")