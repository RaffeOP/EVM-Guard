pragma solidity 0.8.20;

contract Ledger6977 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }

    function totalDeposits() public view returns (uint256) { return reserve; }
}
