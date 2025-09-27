import sys
import os
import subprocess
import threading
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QCheckBox, QTextEdit, QGroupBox, QGridLayout, QSpinBox,
    QProgressBar, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class M3U8Downloader(QMainWindow):
    # 自定义信号，用于在子线程中更新UI
    update_progress = pyqtSignal(int)
    update_log = pyqtSignal(str)
    download_complete = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()
        # 绑定信号和槽
        self.update_progress.connect(self.on_update_progress)
        self.update_log.connect(self.on_update_log)
        self.download_complete.connect(self.on_download_complete)
        # 存储下载线程和进程
        self.download_thread = None
        self.download_process = None
        
        # 初始化高级设置相关属性
        # 字幕设置
        self.sub_only = QCheckBox()
        self.sub_only.setChecked(False)
        self.sub_format = QComboBox()
        self.sub_format.addItems(["SRT", "VTT"])
        self.sub_format.setCurrentText("SRT")
        self.auto_subtitle_fix = QCheckBox()
        self.auto_subtitle_fix.setChecked(True)
        
        # 代理设置
        self.custom_proxy = QLineEdit()
        self.custom_proxy.setPlaceholderText("如 http://127.0.0.1:8888")
        
        # 高级设置
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARN", "ERROR", "OFF"])
        self.log_level.setCurrentText("INFO")
        self.ui_language = QComboBox()
        self.ui_language.addItems(["en-US", "zh-CN", "zh-TW"])
        self.ui_language.setCurrentText("zh-CN")
        self.auto_select = QCheckBox()
        self.auto_select.setChecked(False)
        self.no_log = QCheckBox()
        self.no_log.setChecked(False)
        self.check_segments_count = QCheckBox()
        self.check_segments_count.setChecked(True)
        self.concurrent_download = QCheckBox()
        self.concurrent_download.setChecked(False)
        
        # 解密设置
        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("格式: KID1:KEY1 或直接输入KEY")
        self.decryption_engine = QComboBox()
        self.decryption_engine.addItems(["MP4DECRYPT", "FFMPEG", "SHAKA_PACKAGER"])
        self.decryption_engine.setCurrentText("MP4DECRYPT")
        self.decryption_binary_path = QLineEdit()
        self.mp4_real_time_decryption = QCheckBox()
        self.mp4_real_time_decryption.setChecked(False)
        
        # 自定义参数
        self.args_edit = QLineEdit()
        self.args_edit.setPlaceholderText("输入其他自定义命令行参数")

    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('N_m3u8DL-RE GUI')
        self.setWindowIcon(QIcon("favicon.ico"))
        self.setGeometry(0, 0, 520, 730)
        # 获取屏幕几何信息
        screen_geometry = QApplication.desktop().screenGeometry()
        # 计算窗口居中位置
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        # 禁用最大化按钮
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        # 禁止调整窗口大小
        self.setFixedSize(self.size())
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 执行程序和工作目录
        path_group = QGroupBox("路径设置")
        path_layout = QGridLayout()
        
        path_layout.addWidget(QLabel("执行程序："), 0, 0)
        self.executable_edit = QLineEdit()
        self.executable_edit.setText("N_m3u8DL-RE.exe")
        path_layout.addWidget(self.executable_edit, 0, 1)
        
        browse_btn = QPushButton("选择")
        browse_btn.clicked.connect(self.browse_executable)
        path_layout.addWidget(browse_btn, 0, 2)
        
        path_layout.addWidget(QLabel("工作目录："), 1, 0)
        self.work_dir_edit = QLineEdit()
        path_layout.addWidget(self.work_dir_edit, 1, 1)
        
        dir_btn = QPushButton("选择")
        dir_btn.clicked.connect(self.browse_work_dir)
        path_layout.addWidget(dir_btn, 1, 2)
        
        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)
        
        # M3U8地址和视频标题
        url_group = QGroupBox("下载设置")
        url_layout = QGridLayout()
        
        url_layout.addWidget(QLabel("M3U8地址："), 0, 0)
        self.m3u8_url_edit = QLineEdit()
        url_layout.addWidget(self.m3u8_url_edit, 0, 1)
        
        url_layout.addWidget(QLabel("视频标题："), 1, 0)
        self.title_edit = QLineEdit()
        url_layout.addWidget(self.title_edit, 1, 1)
        
        url_layout.addWidget(QLabel("请求头："), 2, 0)
        self.headers_edit = QLineEdit()
        url_layout.addWidget(self.headers_edit, 2, 1)
        
        url_layout.addWidget(QLabel("BASEURL："), 3, 0)
        self.baseurl_edit = QLineEdit()
        url_layout.addWidget(self.baseurl_edit, 3, 1)
        
        url_layout.addWidget(QLabel("混流文件："), 4, 0)
        self.mux_file_edit = QLineEdit()
        url_layout.addWidget(self.mux_file_edit, 4, 1)
        
        mux_btn = QPushButton("选择")
        mux_btn.clicked.connect(self.browse_mux_file)
        url_layout.addWidget(mux_btn, 4, 2)
        
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)
        
        # 范围选择
        range_group = QGroupBox("范围选择")
        range_layout = QHBoxLayout()
        
        self.start_time_edit = QLineEdit("00:00:00")
        range_layout.addWidget(QLabel("开始时间："))
        range_layout.addWidget(self.start_time_edit)
        
        range_layout.addWidget(QLabel(" - "))
        
        self.end_time_edit = QLineEdit("00:00:00")
        range_layout.addWidget(QLabel("结束时间："))
        range_layout.addWidget(self.end_time_edit)
        
        range_layout.addStretch()
        range_group.setLayout(range_layout)
        main_layout.addWidget(range_group)
        
        # 选项设置 - 基础选项
        options_group = QGroupBox("基础选项")
        options_layout = QGridLayout()
        
        self.del_after_merge = QCheckBox("合并后删除分片")
        self.del_after_merge.setChecked(True)
        options_layout.addWidget(self.del_after_merge, 0, 0)
        
        self.no_date_in_name = QCheckBox("合并时不写入日期")
        self.no_date_in_name.setChecked(True)
        options_layout.addWidget(self.no_date_in_name, 0, 1)
        
        self.no_system_proxy = QCheckBox("不使用系统代理")
        self.no_system_proxy.setChecked(True)
        options_layout.addWidget(self.no_system_proxy, 0, 2)
        
        self.only_parse_m3u8 = QCheckBox("仅解析m3u8")
        options_layout.addWidget(self.only_parse_m3u8, 1, 0)
        
        self.mux_while_download = QCheckBox("混流MP4边下边看")
        options_layout.addWidget(self.mux_while_download, 1, 1)
        
        self.no_merge = QCheckBox("下载完成后不合并")
        options_layout.addWidget(self.no_merge, 1, 2)
        
        self.binary_merge = QCheckBox("使用二进制合并")
        options_layout.addWidget(self.binary_merge, 2, 0)
        
        self.always_on_top = QCheckBox("置顶本窗口")
        self.always_on_top.stateChanged.connect(self.toggle_always_on_top)
        options_layout.addWidget(self.always_on_top, 2, 1)
        
        self.auto_select = QCheckBox("自动选择最佳轨道")
        self.auto_select.setChecked(True)
        options_layout.addWidget(self.auto_select, 2, 2)
        
        self.no_log = QCheckBox("关闭日志文件输出")
        self.no_log.setChecked(False)
        options_layout.addWidget(self.no_log, 3, 0)
        
        self.check_segments_count = QCheckBox("检测分片数量")
        self.check_segments_count.setChecked(True)
        options_layout.addWidget(self.check_segments_count, 3, 1)
        
        self.concurrent_download = QCheckBox("并发下载音视频")
        self.concurrent_download.setChecked(True)
        options_layout.addWidget(self.concurrent_download, 3, 2)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # 性能设置
        performance_group = QGroupBox("性能设置")
        performance_layout = QGridLayout()
        
        performance_layout.addWidget(QLabel("下载线程数："), 0, 0)
        self.max_threads = QSpinBox()
        self.max_threads.setRange(1, 100)
        self.max_threads.setValue(32)
        performance_layout.addWidget(self.max_threads, 0, 1)
        
        performance_layout.addWidget(QLabel("重试次数："), 0, 2)
        self.retry_count = QSpinBox()
        self.retry_count.setRange(1, 100)
        self.retry_count.setValue(15)
        performance_layout.addWidget(self.retry_count, 0, 3)
        
        performance_layout.addWidget(QLabel("HTTP超时(s)："), 0, 4)
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 300)
        self.timeout.setValue(100)  # 根据文档调整为默认值
        performance_layout.addWidget(self.timeout, 0, 5)
        
        performance_layout.addWidget(QLabel("限速(kb/s)："), 1, 0)
        self.limit_speed = QSpinBox()
        self.limit_speed.setRange(0, 10000)
        self.limit_speed.setValue(0)
        performance_layout.addWidget(self.limit_speed, 1, 1)
        
        performance_group.setLayout(performance_layout)
        main_layout.addWidget(performance_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # 按钮
        btn_layout = QHBoxLayout()
        # 输入框显示执行的命令
        self.command_edit = QLineEdit()
        self.command_edit.setReadOnly(True)
        self.command_edit.setFixedWidth(340)
        btn_layout.addWidget(self.command_edit)
        self.go_btn = QPushButton("GO(S)")
        self.go_btn.clicked.connect(self.start_download)
        btn_layout.addWidget(self.go_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        # 日志区域
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        log_layout.addWidget(self.log_edit)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        link_texts = ['<a href="https://ffmpeg.org/download.html">FFmpeg</a>', '<a href="https://github.com/nilaoda/N_m3u8DL-RE/releases">N_m3u8DL-RE</a>', '<a href="https://github.com/wexuo/N_m3u8DL-RE-GUI">N_m3u8DL-RE GUI</a>']
        link_label = QLabel()
        link_label.setOpenExternalLinks(True)
        link_label.setText(" ".join(link_texts))
        
        main_layout.addWidget(link_label)
        
    def browse_executable(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择执行程序", os.getcwd(), "可执行文件 (*.exe);;所有文件 (*)")
        if filename:
            self.executable_edit.setText(filename)
    
    def browse_work_dir(self):
        dirname = QFileDialog.getExistingDirectory(self, "选择工作目录", os.getcwd())
        if dirname:
            self.work_dir_edit.setText(dirname)
    
    def browse_mux_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择混流文件", os.getcwd(), "所有文件 (*)")
        if filename:
            self.mux_file_edit.setText(filename)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "All Files (*)")
        if file_path:
            self.args_edit.setText(f'"{file_path}"')
        
    def browse_decryption_binary(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择解密工具", "", "可执行文件 (*.exe);;所有文件 (*)")
        if file_path:
            self.decryption_binary_path.setText(file_path)
    
    def toggle_always_on_top(self, state):
        if state == Qt.Checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
    
    def start_download(self):
        # 检查必要参数
        if not os.path.exists(self.executable_edit.text()):
            QMessageBox.critical(self, "错误", "执行程序不存在！")
            return
        
        if not self.m3u8_url_edit.text():
            QMessageBox.critical(self, "错误", "请输入M3U8地址！")
            return
        
        # 禁用GO按钮，启用停止按钮
        self.go_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 清空日志和进度条
        self.log_edit.clear()
        self.progress_bar.setValue(0)
        
        # 在新线程中执行下载
        self.download_thread = threading.Thread(target=self.run_download)
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def stop_download(self):
        # 停止下载，真正终止进程
        self.update_log.emit("用户中断下载任务")
        if self.download_process:
            try:
                # 终止下载进程
                if hasattr(self.download_process, 'terminate'):
                    self.download_process.terminate()
                    self.update_log.emit("已尝试终止下载进程")
                # 等待进程终止
                self.download_process.wait(timeout=3)
                if self.download_process.poll() is None:
                    # 如果进程仍在运行，强制终止
                    if hasattr(self.download_process, 'kill'):
                        self.download_process.kill()
                        self.update_log.emit("已强制终止下载进程")
            except Exception as e:
                self.update_log.emit(f"终止进程时出错：{str(e)}")
            finally:
                self.download_process = None
        # 恢复按钮状态
        self.go_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def run_download(self):
        try:
            # 构建命令行参数
            cmd = [self.executable_edit.text()]
            cmd.append(self.m3u8_url_edit.text())
            
            # 添加其他参数
            if self.title_edit.text():
                cmd.extend(["--save-name", self.title_edit.text()])
            
            if self.work_dir_edit.text():
                cmd.extend(["--save-dir", self.work_dir_edit.text()])
            
            if self.headers_edit.text():
                # 处理请求头，支持多个请求头
                headers = self.headers_edit.text().strip()
                if headers:
                    for header in headers.split(';'):
                        header = header.strip()
                        if header:
                            cmd.extend(["-H", header])
            
            if self.baseurl_edit.text():
                cmd.extend(["--base-url", self.baseurl_edit.text()])
            
            if self.mux_file_edit.text():
                cmd.extend(["--mux-import", self.mux_file_edit.text()])
            
            # 范围选择
            if self.start_time_edit.text() != "00:00:00" or self.end_time_edit.text() != "00:00:00":
                range_str = f"{self.start_time_edit.text()}-{self.end_time_edit.text()}"
                cmd.extend(["--custom-range", range_str])
            
            # 选项设置
            if self.del_after_merge.isChecked():
                cmd.append("--del-after-done")
            else:
                cmd.append("--no-del-after-done")
            
            if self.no_date_in_name.isChecked():
                cmd.append("--no-date-info")
            
            if self.no_system_proxy.isChecked():
                cmd.append("--use-system-proxy=false")
            
            if self.only_parse_m3u8.isChecked():
                cmd.append("--skip-download")
            
            if self.mux_while_download.isChecked():
                cmd.append("--live-real-time-merge")
                cmd.append("--live-pipe-mux")
            
            if self.no_merge.isChecked():
                cmd.append("--skip-merge")
            
            if self.binary_merge.isChecked():
                cmd.append("--binary-merge")
                
            cmd.append("--auto-select")
            
            if self.no_log.isChecked():
                cmd.append("--no-log-file")
            
            if self.check_segments_count.isChecked():
                cmd.append("--check-segments-count")
            
            # 性能设置
            cmd.extend(["--thread-count", str(self.max_threads.value())])
            cmd.extend(["--download-retry-count", str(self.retry_count.value())])
            cmd.extend(["--http-request-timeout", str(self.timeout.value())])
            
            if self.limit_speed.value() > 0:
                cmd.extend(["--max-speed", f"{self.limit_speed.value()}K"])
            
            # 字幕设置
            if self.sub_only.isChecked():
                cmd.append("--sub-only")
            
            # 设置字幕格式
            cmd.extend(["--sub-format", self.sub_format.currentText()])
            
            # 自动修正字幕选项
            if not self.auto_subtitle_fix.isChecked():
                cmd.append("--auto-subtitle-fix=false")
            
            # 代理设置
            if self.custom_proxy.text():
                cmd.extend(["--custom-proxy", self.custom_proxy.text()])
            
            # 高级设置
            # 日志级别
            cmd.extend(["--log-level", self.log_level.currentText()])
            
            # UI语言
            cmd.extend(["--ui-language", self.ui_language.currentText()])
            
            # 自动选择最佳轨道
            if self.auto_select.isChecked():
                cmd.append("--auto-select")
            
            # 关闭日志文件输出
            if self.no_log.isChecked():
                cmd.append("--no-log-file")
            
            # 检测分片数量
            if not self.check_segments_count.isChecked():
                cmd.append("--no-segments-count-check")
            
            # 并发下载
            if self.concurrent_download.isChecked():
                cmd.append("--concurrent-download")
            
            # 解密设置
            if self.key_edit.text():
                cmd.extend(["--key", self.key_edit.text()])
            
            cmd.extend(["--decryption-engine", self.decryption_engine.currentText()])
            
            if self.decryption_binary_path.text():
                cmd.extend(["--decryption-binary-path", self.decryption_binary_path.text()])
            
            if self.mp4_real_time_decryption.isChecked():
                cmd.append("--mp4-real-time-decryption")
            
            # 自定义参数
            if self.args_edit.text():
                # 这里需要解析自定义参数，简单处理
                custom_args = self.args_edit.text().split()
                cmd.extend(custom_args)
                
            self.update_log.emit(f"执行命令：{' '.join(cmd)}")
            self.command_edit.setText(' '.join(cmd))
            # 保存进程引用
            self.download_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # 读取输出并更新日志
            for line in iter(self.download_process.stdout.readline, ''):
                self.update_log.emit(line.strip())
                
                # 尝试从输出中提取进度信息
                if "%" in line:
                    try:
                        # 简单解析进度百分比
                        for part in line.split(): 
                            if "%" in part and part[:-1]:
                                progress = int(float(part[:-1]))
                                self.update_progress.emit(progress)
                                break
                    except:
                        pass
            
            # 等待进程结束
            exit_code = self.download_process.wait()
            
            if exit_code == 0:
                self.update_log.emit("下载完成！")
            else:
                self.update_log.emit(f"下载失败，退出代码：{exit_code}")
        
        except Exception as e:
            self.update_log.emit(f"发生错误：{str(e)}")
        
        finally:
            # 重置下载状态
            self.download_thread = None
            self.download_process = None
            self.download_complete.emit()
    
    def on_update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def on_update_log(self, text):
        self.log_edit.append(text)
        # 滚动到底部
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())
    
    def on_download_complete(self):
        # 恢复按钮状态
        self.go_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

if __name__ == '__main__':
    # 确保中文正常显示
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端
    
    app = QApplication(sys.argv)
    
    
    # 设置全局字体
    font = QFont()
    font.setFamily("SimHei")  # 使用黑体字体
    app.setFont(font)
    
    # 创建并显示主窗口
    window = M3U8Downloader()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())