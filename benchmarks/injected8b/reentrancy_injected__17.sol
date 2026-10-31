pragma solidity 0.8.20;

contract Fund2293 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(deposits[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        deposits[msg.sender] -= amount;
        reserve -= amount;
    }

    function balanceOf(address who) public view returns (uint256) { return deposits[who]; }
}
