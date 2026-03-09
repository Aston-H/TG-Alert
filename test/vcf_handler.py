"""
@name: vcf_handler.py
Python 处理 VCF (vCard) 通讯录文件
支持读取、解析、创建、修改 VCF 文件
"""

import vobject
import os

# ==================== 安装依赖 ====================
# pip install vobject

# ==================== 读取 VCF 文件 ====================
def read_vcf_file(file_path):
    """
    读取 VCF 文件并解析所有联系人
    """
    contacts = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        vcf_text = f.read()
    
    # 解析所有 vCard
    for vcard in vobject.readComponents(vcf_text):
        contact = {}
        
        # 获取姓名
        if hasattr(vcard, 'fn'):
            contact['name'] = vcard.fn.value
        
        # 获取电话
        if hasattr(vcard, 'tel_list'):
            contact['phones'] = [tel.value for tel in vcard.tel_list]
        
        # 获取邮箱
        if hasattr(vcard, 'email_list'):
            contact['emails'] = [email.value for email in vcard.email_list]
        
        # 获取地址
        if hasattr(vcard, 'adr_list'):
            contact['addresses'] = [str(adr.value) for adr in vcard.adr_list]
        
        # 获取组织/公司
        if hasattr(vcard, 'org'):
            contact['organization'] = vcard.org.value[0] if vcard.org.value else None
        
        # 获取职位
        if hasattr(vcard, 'title'):
            contact['title'] = vcard.title.value
        
        # 获取备注
        if hasattr(vcard, 'note'):
            contact['note'] = vcard.note.value
        
        contacts.append(contact)
    
    return contacts


def print_contacts(contacts):
    """打印联系人信息"""
    print(f"\n共找到 {len(contacts)} 个联系人:\n")
    print("=" * 60)
    
    for i, contact in enumerate(contacts, 1):
        # print(f"\n[{i}] {contact.get('name', '无名称')}")

        # if contact.get('phones'):
        #     print(f"   📞 电话: {', '.join(contact['phones'])}")
        
        # if contact.get('emails'):
        #     print(f"   📧 邮箱: {', '.join(contact['emails'])}")
        
        # if contact.get('organization'):
        #     print(f"   🏢 公司: {contact['organization']}")
        
        # if contact.get('title'):
        #     print(f"   💼 职位: {contact['title']}")
        
        # if contact.get('note'):
        #     print(f"   📝 备注: {contact['note']}")
        
        # print("-" * 60)
        print(contact)

## ==================== 创建 VCF 文件 ====================
def create_vcf_file(contacts, output_path):
    """
    创建新的 VCF 文件
    
    contacts 格式示例:
    [
        {
            'name': '张三',
            'phones': ['13800138000', '010-12345678'],
            'emails': ['zhangsan@example.com'],
            'organization': 'ABC公司',
            'title': '经理'
        }
    ]
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for contact in contacts:
            vcard = vobject.vCard()
            
            name = contact.get('name', '未命名')
            
            # 添加结构化姓名 (N)
            vcard.add('n')
            # N 格式: 姓;名;中间名;前缀;后缀
            # 中文名字通常只用前两个字段
            vcard.n.value = vobject.vcard.Name(family=name, given='')
            
            # 添加显示名称 (FN)
            vcard.add('fn')
            vcard.fn.value = name
            
            # 添加电话（完整格式）
            if contact.get('phones'):
                for i, phone in enumerate(contact['phones']):
                    tel = vcard.add('tel')
                    tel.value = phone
                    # 设置详细的类型参数
                    if i == 0:
                        # 第一个号码设为首选
                        tel.type_param = ['CELL', ';TYPE=pref', ';TYPE=VOICE']
                    else:
                        tel.type_param = ['CELL', ';TYPE=VOICE']
            
            # 添加邮箱
            if contact.get('emails'):
                for email in contact['emails']:
                    email_obj = vcard.add('email')
                    email_obj.value = email
                    email_obj.type_param = 'INTERNET'
            
            # 添加组织
            if contact.get('organization'):
                vcard.add('org')
                vcard.org.value = [contact['organization']]
            
            # 添加职位
            if contact.get('title'):
                vcard.add('title')
                vcard.title.value = contact['title']
            
            # 添加备注
            if contact.get('note'):
                vcard.add('note')
                vcard.note.value = contact['note']
            
            # 写入文件
            f.write(vcard.serialize())
    
    print(f"✅ VCF 文件已创建: {output_path}")


# ==================== 修改 VCF 文件 ====================
def modify_vcf_file(input_path, output_path, modifications):
    """
    修改 VCF 文件中的联系人
    
    modifications 格式:
    {
        '张三': {'phones': ['新号码'], 'emails': ['新邮箱']}
    }
    """
    contacts = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        vcf_text = f.read()
    
    for vcard in vobject.readComponents(vcf_text):
        name = vcard.fn.value if hasattr(vcard, 'fn') else None
        
        # 如果这个联系人需要修改
        if name in modifications:
            mods = modifications[name]
            
            # 修改电话
            if 'phones' in mods:
                # 删除旧电话
                if hasattr(vcard, 'tel_list'):
                    for tel in vcard.tel_list:
                        vcard.remove(tel)
                
                # 添加新电话
                for phone in mods['phones']:
                    tel = vcard.add('tel')
                    tel.value = phone
                    tel.type_param = 'CELL'
            
            # 修改邮箱
            if 'emails' in mods:
                # 删除旧邮箱
                if hasattr(vcard, 'email_list'):
                    for email in vcard.email_list:
                        vcard.remove(email)
                
                # 添加新邮箱
                for email in mods['emails']:
                    email_obj = vcard.add('email')
                    email_obj.value = email
        
        contacts.append(vcard)
    
    # 保存修改后的文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for vcard in contacts:
            f.write(vcard.serialize())
    
    print(f"✅ VCF 文件已修改: {output_path}")


# ==================== 合并多个 VCF 文件 ====================
def merge_vcf_files(input_files, output_path):
    """合并多个 VCF 文件"""
    all_vcards = []
    
    for file_path in input_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            vcf_text = f.read()
            for vcard in vobject.readComponents(vcf_text):
                all_vcards.append(vcard)
    
    # 保存合并后的文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for vcard in all_vcards:
            f.write(vcard.serialize())
    
    print(f"✅ 已合并 {len(input_files)} 个文件，共 {len(all_vcards)} 个联系人")
    print(f"   输出文件: {output_path}")


# ==================== 导出为其他格式 ====================
def vcf_to_csv(vcf_path, csv_path):
    """将 VCF 转换为 CSV"""
    import csv
    
    contacts = read_vcf_file(vcf_path)
    
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['姓名', '电话', '邮箱', '公司', '职位', '备注'])
        
        for contact in contacts:
            writer.writerow([
                contact.get('name', ''),
                ', '.join(contact.get('phones', [])),
                ', '.join(contact.get('emails', [])),
                contact.get('organization', ''),
                contact.get('title', ''),
                contact.get('note', '')
            ])
    
    print(f"✅ 已导出为 CSV: {csv_path}")


def vcf_to_json(vcf_path, json_path):
    """将 VCF 转换为 JSON"""
    import json
    
    contacts = read_vcf_file(vcf_path)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已导出为 JSON: {json_path}")


# ==================== 使用示例 ====================
if __name__ == '__main__':
    
    # # 示例1: 读取 VCF 文件
    # print("\n【示例1: 读取 VCF 文件】")
    # try:
    #     contacts = read_vcf_file('/Users/huangcheng/Downloads/通讯录.vcf')
    #     print_contacts(contacts)
    # except FileNotFoundError:
    #     print("⚠️  文件 contacts.vcf 不存在，跳过示例1")
    
    
#     # 示例2: 创建新的 VCF 文件
#     print("\n【示例2: 创建新的 VCF 文件】")
    new_contacts = [
        

    ]
    create_vcf_file(new_contacts, 'new_contacts.vcf')
    
    
    # 示例3: 转换为 CSV
    # print("\n【示例3: 转换为 CSV】")
    # vcf_to_csv('new_contacts.vcf', 'contacts.csv')
    
    
    # # 示例4: 转换为 JSON
    # print("\n【示例4: 转换为 JSON】")
    # vcf_to_json('', 'contacts2.json')
    
    
    # # 示例5: 合并多个 VCF 文件
    # print("\n【示例5: 合并 VCF 文件】")
    # # merge_vcf_files(['file1.vcf', 'file2.vcf'], 'merged.vcf')
    
    # print("\n✅ 所有示例执行完成!")