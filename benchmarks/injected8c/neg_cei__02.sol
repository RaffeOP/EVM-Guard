pragma solidity 0.8.20;

contract Treasury1010 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        reserve -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }
}
